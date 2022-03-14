package diptestbed.database.services

import scala.concurrent.ExecutionContext
import cats.effect.Async
import cats.implicits._
import diptestbed.database.catalog.HardwareAccessCatalog.HardwareAccessTable
import diptestbed.database.catalog.HardwareCatalog.{HardwareRow, HardwareTable, toDomain => hardwareToDomain}
import diptestbed.database.catalog.UserCatalog.UserTable
import diptestbed.database.driver.DatabaseDriverOps._
import diptestbed.database.driver.DatabaseOutcome.DatabaseResult
import diptestbed.domain.{Hardware, HardwareId, User, UserId}
import slick.dbio.DBIOAction.sequenceOption

class HardwareService[F[_]: Async](
  val hardwareTable: HardwareTable,
  val hardwareAccessTable: HardwareAccessTable,
  val userTable: UserTable,
)(implicit executionContext: ExecutionContext) {
  import hardwareTable.dbDriver.profile.api._
  import hardwareTable._
  import hardwareAccessTable.HardwareAccessQuery
  import hardwareAccessTable.HardwareAccessTable
  import userTable.UserQuery

  def countAllHardware(): F[DatabaseResult[Int]] =
    HardwareQuery.length.result.tryRunDBIO(dbDriver)

  def createHardware(
    name: String,
    ownerId: UserId,
    isPublic: Boolean,
  ): F[DatabaseResult[Option[Hardware]]] = {
    val row = HardwareRow(name = name, ownerId = ownerId.value, isPublic = isPublic)
    val hardwareCreation: DBIOAction[Option[Int], NoStream, Effect.Read with Effect.Write] =
      for {
        existingOwner <- UserQuery.filter(_.uuid === ownerId.value).result.headOption
        hardwareCreation <- sequenceOption(Option.when(existingOwner.isDefined)(HardwareQuery += row))
      } yield hardwareCreation

    hardwareCreation
      .tryRunDBIO(dbDriver)
      .map(dbioAction => dbioAction.map(hardwareId => hardwareId.map(_ => hardwareToDomain(row))))
  }

  def accessibleHardwareQuery(requester: Option[User]): Query[hardwareTable.HardwareTable, HardwareRow, Seq] =
    requester match {
      // If no requester, then assuming full accessibility
      case None => HardwareQuery
      case Some(user) =>
        HardwareQuery
          // Requester must be a hardware owner or have explicit hardware access
          .joinLeft(HardwareAccessQuery)
          .on((h, a) => h.uuid === a.hardwareId)
          .filter { case (h, a) =>
            a.map(_.userId) === user.id.value || h.ownerUuid === user.id.value
          }
          .map { case (h, _) => h }
    }

  def getHardware(requester: Option[User], id: HardwareId): F[DatabaseResult[Option[Hardware]]] =
    accessibleHardwareQuery(requester)
      .filter(_.uuid === id.value)
      .result
      .headOption
      .map(_.map(hardwareToDomain))
      .tryRunDBIO(dbDriver)

  def getHardwares(requester: Option[User]): F[DatabaseResult[Seq[Hardware]]] = {
    accessibleHardwareQuery(requester)
      .result
      .map(_.map(hardwareToDomain))
      .tryRunDBIO(dbDriver)
  }

}
