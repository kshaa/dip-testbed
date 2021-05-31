package iotfrisbee.database.services

import scala.concurrent.ExecutionContext
import cats.implicits._
import cats.effect.Async
import iotfrisbee.database.catalog.DiskGolfTrackCatalog.{
  DiskGolfTrackRow,
  DiskGolfTrackTable,
  toDomain => diskGolfTrackToDomain,
}
import iotfrisbee.database.catalog.UserCatalog.UserTable
import iotfrisbee.domain.{DiskGolfTrack, DiskGolfTrackId, DomainTimeZoneId, UserId}
import iotfrisbee.database.driver.DatabaseDriverOps._
import iotfrisbee.database.driver.DatabaseOutcome.DatabaseResult
import slick.dbio.DBIOAction.sequenceOption

class DiskGolfTrackService[F[_]: Async](
  val diskGolfTrackTable: DiskGolfTrackTable,
  val userTable: UserTable,
)(implicit executionContext: ExecutionContext) {
  import diskGolfTrackTable.dbDriver.profile.api._
  import diskGolfTrackTable._
  import userTable.UserQuery

  def countDiskGolfTracks(): F[DatabaseResult[Int]] =
    DiskGolfTrackQuery.length.result.tryRunDBIO(dbDriver)

  def createDiskGolfTrack(
    ownerId: UserId,
    name: String,
    timezoneId: DomainTimeZoneId,
  ): F[DatabaseResult[Option[DiskGolfTrack]]] = {
    val row = DiskGolfTrackRow(ownerUUID = ownerId.value, name = name, timezone = timezoneId.value)

    val diskGolfTrackCreation: DBIOAction[Option[Int], NoStream, Effect.Read with Effect.Write] =
      for {
        existingOwner <- UserQuery.filter(_.uuid === ownerId.value).result.headOption
        diskGolfTrackCreation <- sequenceOption(Option.when(existingOwner.isDefined)(DiskGolfTrackQuery += row))
      } yield diskGolfTrackCreation

    diskGolfTrackCreation
      .tryRunDBIO(dbDriver)
      .map(_.map(_.map(_ => diskGolfTrackToDomain(row))))
  }

  def getDiskGolfTrack(id: DiskGolfTrackId): F[DatabaseResult[Option[DiskGolfTrack]]] =
    DiskGolfTrackQuery
      .filter(_.uuid === id.value)
      .result
      .headOption
      .map(_.map(diskGolfTrackToDomain))
      .tryRunDBIO(dbDriver)

  def getDiskGolfTracks: F[DatabaseResult[Seq[DiskGolfTrack]]] =
    DiskGolfTrackQuery.result
      .map(_.map(diskGolfTrackToDomain))
      .tryRunDBIO(dbDriver)

}
