package iotfrisbee.database.services

import scala.concurrent.ExecutionContext
import cats.effect.Async
import cats.implicits._
import iotfrisbee.database.catalog.HardwareCatalog.{HardwareRow, HardwareTable, toDomain => hardwareToDomain}
import iotfrisbee.database.catalog.UserCatalog.UserTable
import iotfrisbee.database.driver.DatabaseDriverOps._
import iotfrisbee.database.driver.DatabaseOutcome.DatabaseResult
import iotfrisbee.domain.{Hardware, HardwareId, UserId}
import slick.dbio.DBIOAction.sequenceOption

class HardwareService[F[_]: Async](
  val hardwareTable: HardwareTable,
  val userTable: UserTable,
)(implicit executionContext: ExecutionContext) {
  import hardwareTable.dbDriver.profile.api._
  import hardwareTable._
  import userTable.UserQuery

  def countHardware(): F[DatabaseResult[Int]] =
    HardwareQuery.length.result.tryRunDBIO(dbDriver)

  def createHardware(
    name: String,
    ownerId: UserId,
  ): F[DatabaseResult[Option[Hardware]]] = {
    val row = HardwareRow(name = name, ownerId = ownerId.value)
    val hardwareCreation: DBIOAction[Option[Int], NoStream, Effect.Read with Effect.Write] =
      for {
        existingOwner <- UserQuery.filter(_.uuid === ownerId.value).result.headOption
        hardwareCreation <- sequenceOption(Option.when(existingOwner.isDefined)(HardwareQuery += row))
      } yield hardwareCreation

    hardwareCreation
      .tryRunDBIO(dbDriver)
      .map(dbioAction => dbioAction.map(hardwareId => hardwareId.map(_ => hardwareToDomain(row))))
  }

  def getHardware(id: HardwareId): F[DatabaseResult[Option[Hardware]]] =
    HardwareQuery
      .filter(_.uuid === id.value)
      .result
      .headOption
      .map(_.map(hardwareToDomain))
      .tryRunDBIO(dbDriver)

  def getHardwares: F[DatabaseResult[Seq[Hardware]]] =
    HardwareQuery.result
      .map(_.map(hardwareToDomain))
      .tryRunDBIO(dbDriver)

}
