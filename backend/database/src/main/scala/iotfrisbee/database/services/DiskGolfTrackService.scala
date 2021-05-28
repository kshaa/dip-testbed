package iotfrisbee.database.services

import scala.concurrent.ExecutionContext
import cats.implicits._
import cats.effect.Async
import iotfrisbee.database.catalog.DiskGolfTrackCatalog.{
  DiskGolfTrackRow,
  DiskGolfTrackTable,
  toDomain => diskGolfTrackToDomain,
}
import iotfrisbee.database.driver.DatabaseDriver.JdbcDatabaseDriver
import iotfrisbee.domain.{DiskGolfTrack, DiskGolfTrackId, DomainTimeZoneId, UserId}
import iotfrisbee.database.driver.DatabaseDriverOps._
import iotfrisbee.database.driver.DatabaseOutcome.DatabaseResult

class DiskGolfTrackService[F[_]: Async](
  val dbDriver: JdbcDatabaseDriver,
  val diskGolfTrackTable: DiskGolfTrackTable,
)(implicit executionContext: ExecutionContext) {
  import dbDriver.profile.api._
  import diskGolfTrackTable._

  def countDiskGolfTracks(): F[DatabaseResult[Int]] =
    DiskGolfTrackQuery.length.result.tryRunDBIO(dbDriver)

  def createDiskGolfTrack(
    ownerId: UserId,
    name: String,
    timezoneId: DomainTimeZoneId,
  ): F[DatabaseResult[DiskGolfTrack]] = {
    val row = DiskGolfTrackRow(ownerUUID = ownerId.value, name = name, timezone = timezoneId.value)
    (DiskGolfTrackQuery += row)
      .tryRunDBIO(dbDriver)
      .map(_.map(_ => diskGolfTrackToDomain(row)))
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
