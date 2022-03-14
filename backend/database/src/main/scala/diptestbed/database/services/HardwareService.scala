package diptestbed.database.services

import cats.data.EitherT
import scala.concurrent.ExecutionContext
import cats.effect.Async
import cats.implicits._
import diptestbed.database.catalog.HardwareAccessCatalog.{HardwareAccessRow, HardwareAccessTable}
import diptestbed.database.catalog.HardwareCatalog.{HardwareRow, HardwareTable, toDomain => hardwareToDomain}
import diptestbed.database.catalog.UserCatalog.UserTable
import diptestbed.database.driver.DatabaseDriverOps._
import diptestbed.database.driver.DatabaseOutcome.{DatabaseException, DatabaseResult}
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

  def accessibleHardwareQuery(requester: Option[User], write: Boolean): Query[hardwareTable.HardwareTable, HardwareRow, Seq] =
    requester match {
      case None => HardwareQuery
      case Some(user) if user.isManager => HardwareQuery
      case Some(user) =>
        HardwareQuery
          // Requester must be a hardware owner or have explicit hardware access
          .joinLeft(HardwareAccessQuery)
          .on((h, a) => h.uuid === a.hardwareId)
          .filter { case (h, a) =>
            (h.isPublic && !write) || a.map(_.userId).filter(_ => !write) === user.id.value || h.ownerUuid === user.id.value
          }
          .distinctOn { case (h, _) => h.uuid }
          .map { case (h, _) => h }
    }

  def getHardware(requester: Option[User], id: HardwareId, write: Boolean): F[DatabaseResult[Option[Hardware]]] =
    accessibleHardwareQuery(requester, write)
      .filter(_.uuid === id.value)
      .result
      .headOption
      .map(_.map(hardwareToDomain))
      .tryRunDBIO(dbDriver)

  def getHardwares(requester: Option[User], write: Boolean): F[DatabaseResult[Seq[Hardware]]] = {
    accessibleHardwareQuery(requester, write)
      .result
      .map(_.map(hardwareToDomain))
      .tryRunDBIO(dbDriver)
  }

  def getManageableHardware(manager: Option[User], accessUserId: UserId): F[DatabaseResult[Seq[(Hardware, Boolean)]]] = {
    accessibleHardwareQuery(manager, write = false)
      .joinLeft(HardwareAccessQuery)
      .on((h, a) => h.uuid === a.hardwareId && a.userId === accessUserId.value)
      .distinctOn { case (h, _) => h.uuid }
      .map { case (h, a) => (h, a.isDefined || h.isPublic) }
      .result
      .map(_.map { case (h, a) => (hardwareToDomain(h), a) })
      .tryRunDBIO(dbDriver)
  }

  def setHardwareAccess(
    requester: Option[User],
    userId: UserId,
    hardwareId: HardwareId,
    isAccessible: Boolean
  ): F[DatabaseResult[Int]] = {
    val additionQuery = HardwareAccessQuery += HardwareAccessRow(hardwareId.value, userId.value)
    val deletionQuery =
      HardwareAccessQuery
        .filter(a => a.userId === userId.value && a.hardwareId === hardwareId.value)
        .delete

    if (isAccessible) {
      requester match {
        case None => additionQuery.tryRunDBIO(dbDriver)
        case Some(user) if user.isManager => additionQuery.tryRunDBIO(dbDriver)
        case Some(user) =>
          (for {
            requesterAccessibleHardwareId <- EitherT(getHardware(Some(user), hardwareId, write = true))
            _ <- EitherT.fromEither[F](Either.cond(requesterAccessibleHardwareId.isDefined, (), DatabaseException(new Exception("Entity already exists"))))
            userCreation <- EitherT(additionQuery.tryRunDBIO(dbDriver))
          } yield userCreation).value
      }
    } else {
      requester match {
        case None => deletionQuery.tryRunDBIO(dbDriver)
        case Some(user) if user.isManager => deletionQuery.tryRunDBIO(dbDriver)
        case Some(user) =>
          (for {
            requesterAccessibleHardwareId <- EitherT(getHardware(Some(user), hardwareId, write = true))
            _ <- EitherT.fromEither[F](Either.cond(requesterAccessibleHardwareId.isDefined, (), DatabaseException(new Exception("Entity already exists"))))
            deletion <- EitherT(deletionQuery.tryRunDBIO(dbDriver))
          } yield deletion).value

      }
    }
  }

  def setPublic(requester: Option[User], id: HardwareId, isPublic: Boolean): EitherT[F, DatabaseException, Int] = {
    for {
      requesterAccessibleHardware <- EitherT(getHardware(requester, id, write = true))
      _ <- EitherT.fromEither[F](Either.cond(requesterAccessibleHardware.isDefined, (), DatabaseException(new Exception("Entity not managable"))))
      result <- EitherT(HardwareQuery.filter(_.uuid === id.value).map(_.isPublic).update(isPublic).tryRunDBIO(dbDriver))
    } yield result
  }
}
