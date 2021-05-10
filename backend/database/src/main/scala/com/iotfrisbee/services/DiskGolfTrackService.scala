package com.iotfrisbee.services

import cats.effect.IO
import com.google.inject.Inject
import com.iotfrisbee.catalog.DiskGolfTrackCatalog.{
  DiskGolfTrackTable,
  toDomain => diskGolfTrackToDomain,
}
import com.iotfrisbee.{DiskGolfTrack, DiskGolfTrackUUID}
import javax.inject.Singleton
import play.api.db.slick.DatabaseConfigProvider
import slick.basic.DatabaseConfig
import slick.jdbc.JdbcProfile

import scala.concurrent.ExecutionContext.Implicits.global

@Singleton
class DiskGolfTrackService @Inject() (
    dbConfigProvider: DatabaseConfigProvider,
    diskGolfTrackTable: DiskGolfTrackTable,
) {
  private val dbConfig: DatabaseConfig[JdbcProfile] =
    dbConfigProvider.get[JdbcProfile]
  import dbConfig._
  import profile.api._
  import diskGolfTrackTable._

  def getDiskGolfTrackById(id: DiskGolfTrackUUID): IO[Option[DiskGolfTrack]] =
    IO.fromFuture(
      IO(
        db.run(
          DiskGolfTrackQuery
            .filter(_.uuid === id.value)
            .result
            .headOption
            .map(_.map(diskGolfTrackToDomain)),
        ),
      ),
    )

  def countDiskGolfTracks(): IO[Int] =
    IO.fromFuture(IO(db.run(DiskGolfTrackQuery.length.result)))
}
