package diptestbed.database.services

import cats.effect.Async
import cats.implicits._
import diptestbed.database.catalog.SoftwareCatalog.{SoftwareRow, SoftwareTable}
import diptestbed.database.catalog.UserCatalog.UserTable
import diptestbed.database.driver.DatabaseDriverOps._
import diptestbed.database.driver.DatabaseOutcome.DatabaseResult
import diptestbed.domain.{Software, SoftwareId, SoftwareMeta, UserId}
import slick.dbio.DBIOAction.sequenceOption
import scala.concurrent.ExecutionContext

class SoftwareService[F[_]: Async](
  val softwareTable: SoftwareTable,
  val userTable: UserTable,
)(implicit executionContext: ExecutionContext) {
  import softwareTable._
  import softwareTable.dbDriver.profile.api._
  import userTable.UserQuery

  def countSoftware(): F[DatabaseResult[Int]] =
    SoftwareQuery.length.result.tryRunDBIO(dbDriver)

  def createSoftware(
    name: String,
    ownerId: UserId,
    content: Array[Byte],
  ): F[DatabaseResult[Option[SoftwareMeta]]] = {
    val row = SoftwareRow(name = name, ownerId = ownerId.value, content = content)
    val softwareCreation: DBIOAction[Option[Int], NoStream, Effect.Read with Effect.Write] =
      for {
        existingOwner <- UserQuery.filter(_.uuid === ownerId.value).result.headOption
        softwareCreation <- sequenceOption(Option.when(existingOwner.isDefined)(SoftwareQuery += row))
      } yield softwareCreation

    softwareCreation
      .tryRunDBIO(dbDriver)
      .map(dbioAction =>
        dbioAction
          .map(softwareId => softwareId.map(_ => SoftwareMeta(SoftwareId(row.id), UserId(row.ownerId), row.name))),
      )
  }

  def getSoftware(id: SoftwareId): F[DatabaseResult[Option[Software]]] =
    SoftwareQuery
      .filter(_.uuid === id.value)
      .result
      .headOption
      .map(_.map(row => Software(SoftwareMeta(SoftwareId(row.id), UserId(row.ownerId), row.name), row.content)))
      .tryRunDBIO(dbDriver)

  def getSoftwareMeta(id: SoftwareId): F[DatabaseResult[Option[SoftwareMeta]]] =
    SoftwareQuery
      .filter(_.uuid === id.value)
      .map(row => (row.uuid, row.ownerUuid, row.name))
      .result
      .headOption
      .map(_.map {
        case (id, ownerId, name) =>
          SoftwareMeta(SoftwareId(id), UserId(ownerId), name)
      })
      .tryRunDBIO(dbDriver)

  def getSoftwareMetas: F[DatabaseResult[Seq[SoftwareMeta]]] =
    SoftwareQuery
      .map(row => (row.uuid, row.ownerUuid, row.name))
      .result
      .map(_.map {
        case (id, ownerId, name) =>
          SoftwareMeta(SoftwareId(id), UserId(ownerId), name)
      })
      .tryRunDBIO(dbDriver)

}
