package iotfrisbee.database.services

import java.util.UUID
import scala.concurrent.ExecutionContext
import cats.effect.Async
import cats.implicits._
import slick.dbio.DBIOAction.sequenceOption
import iotfrisbee.database.catalog.DiskGolfDiskCatalog.{
  DiskGolfDiskRow,
  DiskGolfDiskTable,
  toDomain => diskGolfDiskToDomain,
}
import iotfrisbee.database.catalog.DiskGolfTrackCatalog.DiskGolfTrackTable
import iotfrisbee.database.catalog.HardwareCatalog.HardwareTable
import iotfrisbee.database.driver.DatabaseDriver.existsOrError
import iotfrisbee.database.driver.DatabaseDriverOps._
import iotfrisbee.database.driver.DatabaseOutcome.DatabaseResult
import iotfrisbee.database.services.DiskGolfDiskService._
import iotfrisbee.domain.{DiskGolfDisk, DiskGolfDiskId, DiskGolfTrackId, HardwareId}

class DiskGolfDiskService[F[_]: Async](
  val diskGolfDiskTable: DiskGolfDiskTable,
  val diskGolfTrackTable: DiskGolfTrackTable,
  val hardwareTable: HardwareTable,
)(implicit executionContext: ExecutionContext) {
  import diskGolfDiskTable._
  import diskGolfDiskTable.dbDriver.profile.api._
  import diskGolfTrackTable.DiskGolfTrackQuery
  import hardwareTable.HardwareQuery

  def countDiskGolfDisks(): F[DatabaseResult[Int]] =
    DiskGolfDiskQuery.length.result.tryRunDBIO(dbDriver)

  def createDiskGolfDisk(
    name: String,
    trackId: DiskGolfTrackId,
    hardwareId: Option[HardwareId],
  ): F[DatabaseResult[Either[List[DiskGolfDiskCreationError], DiskGolfDisk]]] = {
    val row = DiskGolfDiskRow(name = name, trackUUID = trackId.value, hardwareUUID = hardwareId.map(_.value))

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

    // N.B.: Without "Serializable" isolation technically a track/hardware could exist but get removed while transacting
    // which would lead to a nevertheless committed row with a non-existent foreign key reference
    val diskGolfDiskCreation
      : DBIOAction[Either[List[DiskGolfDiskCreationError], Int], NoStream, Effect.Read with Effect.Write] =
      for {
        existenceTrackError <- existsOrError(trackCheck, NonExistentTrack)
        existenceHardwareError <-
          existsOrError(hardwareCheck, NonExistentHardware).map(_.flatMap(Option.when(hardwareId.nonEmpty)(_)))
        existenceErrors = (existenceTrackError :: existenceHardwareError :: Nil).flatten
        diskGolfTrackCreation <-
          sequenceOption(Option.when(existenceErrors.isEmpty)(DiskGolfDiskQuery += row)).map(_.toRight(existenceErrors))
      } yield diskGolfTrackCreation

    diskGolfDiskCreation
      .tryRunDBIO(dbDriver)
      .map(_.map(_.map(_ => diskGolfDiskToDomain(row))))
  }

  def getDiskGolfDisk(id: DiskGolfDiskId): F[DatabaseResult[Option[DiskGolfDisk]]] =
    DiskGolfDiskQuery
      .filter(_.uuid === id.value)
      .result
      .headOption
      .map(_.map(diskGolfDiskToDomain))
      .tryRunDBIO(dbDriver)

  def getDiskGolfTracks: F[DatabaseResult[Seq[DiskGolfDisk]]] =
    DiskGolfDiskQuery.result
      .map(_.map(diskGolfDiskToDomain))
      .tryRunDBIO(dbDriver)

}

object DiskGolfDiskService {
  sealed trait DiskGolfDiskCreationError
  case object NonExistentTrack extends DiskGolfDiskCreationError
  case object NonExistentHardware extends DiskGolfDiskCreationError
}
