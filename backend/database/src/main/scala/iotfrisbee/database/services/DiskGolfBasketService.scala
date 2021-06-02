package iotfrisbee.database.services

import java.util.UUID
import scala.concurrent.ExecutionContext
import slick.dbio.DBIOAction.sequenceOption
import cats.effect.Async
import cats.implicits._
import iotfrisbee.database.catalog.DiskGolfBasketCatalog.{
  DiskGolfBasketRow,
  DiskGolfBasketTable,
  toDomain => diskGolfBasketToDomain,
}
import iotfrisbee.database.catalog.DiskGolfTrackCatalog.DiskGolfTrackTable
import iotfrisbee.database.catalog.HardwareCatalog.HardwareTable
import iotfrisbee.database.driver.DatabaseDriverOps._
import iotfrisbee.database.driver.DatabaseOutcome.DatabaseResult
import iotfrisbee.database.services.DiskGolfBasketService._
import iotfrisbee.domain._

class DiskGolfBasketService[F[_]: Async](
  val diskGolfBasketTable: DiskGolfBasketTable,
  val diskGolfTrackTable: DiskGolfTrackTable,
  val hardwareTable: HardwareTable,
)(implicit executionContext: ExecutionContext) {
  import diskGolfBasketTable._
  import diskGolfBasketTable.dbDriver.profile.api._
  import diskGolfTrackTable.DiskGolfTrackQuery
  import hardwareTable.HardwareQuery

  def countDiskGolfBaskets(): F[DatabaseResult[Int]] =
    DiskGolfBasketQuery.length.result.tryRunDBIO(dbDriver)

  def createDiskGolfBasket(
    name: String,
    trackId: DiskGolfTrackId,
    hardwareId: Option[HardwareId],
  ): F[DatabaseResult[Either[List[DiskGolfBasketCreationError], DiskGolfBasket]]] = {
    def row(orderNumber: Int) =
      DiskGolfBasketRow(
        name = name,
        orderNumber = orderNumber,
        trackUUID = trackId.value,
        hardwareUUID = hardwareId.map(_.value),
      )

    val lastOrderNumberCheck: DBIOAction[Int, NoStream, Effect.Read] =
      DiskGolfBasketQuery
        .filter(_.trackUUID === trackId.value)
        .map(_.orderNumber)
        .sorted(_.desc)
        .result
        .headOption
        .map(_.getOrElse(-1))

    val trackCheck: DBIOAction[Option[UUID], NoStream, Effect.Read] =
      DiskGolfTrackQuery
        .filter(_.uuid === trackId.value)
        .map(_.uuid)
        .result
        .headOption

    val hardwareCheck: DBIOAction[Option[UUID], NoStream, Effect.Read] =
      sequenceOption(
        hardwareId.map(hardwareUUID =>
          HardwareQuery.filter(_.uuid === hardwareUUID.value).map(_.uuid).result.headOption,
        ),
      ).map(_.flatten)

    val diskGolfBasketCreatedOrderNumber
      : DBIOAction[Either[List[DiskGolfBasketCreationError], Int], NoStream, Effect.Read with Effect.Write] =
      for {
        existenceTrackError <-
          trackCheck.map(_.fold[Option[DiskGolfBasketCreationError]](Some(NonExistentTrack))(_ => None))

        existenceHardwareError <-
          hardwareCheck
            .map(_.fold[Option[DiskGolfBasketCreationError]](Some(NonExistentHardware))(_ => None))
            .map(_.flatMap(error => Option.when(hardwareId.nonEmpty)(error)))

        existenceErrors = (existenceTrackError :: existenceHardwareError :: Nil).flatten

        lastOrderNumber <- lastOrderNumberCheck
        newOrderNumber = lastOrderNumber + 1

        createdOrderNumber <- (DiskGolfBasketQuery += row(newOrderNumber)).map(_ => newOrderNumber)

        createdOrderNumberOrErrors = Option.when(existenceErrors.nonEmpty)(existenceErrors).toLeft(createdOrderNumber)
      } yield createdOrderNumberOrErrors

    diskGolfBasketCreatedOrderNumber
      .tryRunDBIO(dbDriver)
      .map(_.map(_.map(orderNumber => diskGolfBasketToDomain(row(orderNumber)))))
  }

  def getDiskGolfBasket(id: DiskGolfBasketId): F[DatabaseResult[Option[DiskGolfBasket]]] =
    DiskGolfBasketQuery
      .filter(_.uuid === id.value)
      .result
      .headOption
      .map(_.map(diskGolfBasketToDomain))
      .tryRunDBIO(dbDriver)

  def getDiskGolfBaskets: F[DatabaseResult[Seq[DiskGolfBasket]]] =
    DiskGolfBasketQuery.result
      .map(_.map(diskGolfBasketToDomain))
      .tryRunDBIO(dbDriver)

}

object DiskGolfBasketService {
  sealed trait DiskGolfBasketCreationError
  case object NonExistentTrack extends DiskGolfBasketCreationError
  case object NonExistentHardware extends DiskGolfBasketCreationError
}
