package iotfrisbee.database.services

import cats.effect.Async
import iotfrisbee.database.catalog.DiskGolfTrackCatalog.{DiskGolfTrackTable, toDomain => diskGolfTrackToDomain}
import iotfrisbee.database.driver.DatabaseDriver.JdbcDatabaseDriver
import iotfrisbee.domain.{DiskGolfTrack, DiskGolfTrackUUID}
import iotfrisbee.database.driver.DatabaseDriverOps._
import iotfrisbee.database.driver.DatabaseOutcome.DatabaseResult
import scala.concurrent.ExecutionContext

class DiskGolfTrackService[F[_]: Async](
  val dbDriver: JdbcDatabaseDriver,
  val diskGolfTrackTable: DiskGolfTrackTable,
)(implicit executionContext: ExecutionContext) {
  import dbDriver.profile.api._
  import diskGolfTrackTable._

  def getDiskGolfTrackById(id: DiskGolfTrackUUID): F[DatabaseResult[Option[DiskGolfTrack]]] =
    DiskGolfTrackQuery
      .filter(_.uuid === id.value)
      .result
      .headOption
      .map(_.map(diskGolfTrackToDomain))
      .tryRunDBIO(dbDriver)

  def countDiskGolfTracks(): F[DatabaseResult[Int]] =
    DiskGolfTrackQuery.length.result.tryRunDBIO(dbDriver)
}
