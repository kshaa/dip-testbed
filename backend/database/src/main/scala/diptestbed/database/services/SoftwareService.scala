package diptestbed.database.services

import cats.effect.Async
import cats.implicits._
import diptestbed.database.catalog.SoftwareCatalog.{SoftwareRow, SoftwareTable}
import diptestbed.database.catalog.UserCatalog.UserTable
import diptestbed.database.driver.DatabaseDriverOps._
import diptestbed.database.driver.DatabaseOutcome.DatabaseResult
import diptestbed.domain.{Software, SoftwareId, SoftwareMeta, User, UserId}
import slick.dbio.DBIOAction.sequenceOption

import scala.concurrent.ExecutionContext

class SoftwareService[F[_]: Async](
  val softwareTable: SoftwareTable,
  val userTable: UserTable,
)(implicit executionContext: ExecutionContext) {
  import softwareTable._
  import softwareTable.dbDriver.profile.api._
  import userTable.UserQuery

  def countAllSoftware(): F[DatabaseResult[Int]] =
    SoftwareQuery.length.result.tryRunDBIO(dbDriver)

  def createSoftware(
    name: String,
    ownerId: UserId,
    isPublic: Boolean,
    content: Array[Byte],
  ): F[DatabaseResult[Option[SoftwareMeta]]] = {
    val row = SoftwareRow(name = name, ownerId = ownerId.value, content = content, isPublic = isPublic)
    val softwareCreation: DBIOAction[Option[Int], NoStream, Effect.Read with Effect.Write] =
      for {
        existingOwner <- UserQuery.filter(_.uuid === ownerId.value).result.headOption
        softwareCreation <- sequenceOption(Option.when(existingOwner.isDefined)(SoftwareQuery += row))
      } yield softwareCreation

    softwareCreation
      .tryRunDBIO(dbDriver)
      .map(dbioAction =>
        dbioAction
          .map(softwareId => softwareId.map(_ =>
            SoftwareMeta(SoftwareId(row.id), UserId(row.ownerId), row.name, isPublic))),
      )
  }

  def accessibleSoftwareQuery(requester: Option[User]): Query[softwareTable.SoftwareTable, SoftwareRow, Seq] =
    requester match {
      // If no requester, then assuming full accessibility
      case None => SoftwareQuery
      case Some(user) if user.isManager => SoftwareQuery
      case Some(user) => SoftwareQuery.filter(s => s.ownerUuid === user.id.value)
    }

  def getSoftware(requester: Option[User], id: SoftwareId): F[DatabaseResult[Option[Software]]] =
    accessibleSoftwareQuery(requester)
      .filter(_.uuid === id.value)
      .result
      .headOption
      .map(_.map(row =>
        Software(SoftwareMeta(SoftwareId(row.id), UserId(row.ownerId), row.name, row.isPublic), row.content)))
      .tryRunDBIO(dbDriver)

  def getSoftwareMeta(requester: Option[User], id: SoftwareId): F[DatabaseResult[Option[SoftwareMeta]]] =
    accessibleSoftwareQuery(requester)
      .filter(_.uuid === id.value)
      .map(row => (row.uuid, row.ownerUuid, row.name, row.isPublic))
      .result
      .headOption
      .map(_.map {
        case (id, ownerId, name, isPublic) =>
          SoftwareMeta(SoftwareId(id), UserId(ownerId), name, isPublic)
      })
      .tryRunDBIO(dbDriver)

  def getSoftwareMetas(requester: Option[User]): F[DatabaseResult[Seq[SoftwareMeta]]] =
    accessibleSoftwareQuery(requester)
      .map(row => (row.uuid, row.ownerUuid, row.name, row.isPublic))
      .result
      .map(_.map {
        case (id, ownerId, name, isPublic) =>
          SoftwareMeta(SoftwareId(id), UserId(ownerId), name, isPublic)
      })
      .tryRunDBIO(dbDriver)

}
