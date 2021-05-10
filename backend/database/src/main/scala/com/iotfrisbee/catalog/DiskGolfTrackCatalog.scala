package com.iotfrisbee.catalog

import java.util.{TimeZone, UUID}
import com.google.inject.Inject
import com.iotfrisbee.{DiskGolfTrack, DiskGolfTrackUUID, UserId}
import javax.inject.Singleton
import play.api.db.slick.DatabaseConfigProvider
import slick.basic.DatabaseConfig
import slick.jdbc.JdbcProfile
import slick.lifted.ProvenShape

object DiskGolfTrackCatalog {

  @Singleton
  class DiskGolfTrackTable @Inject() (
      dbConfigProvider: DatabaseConfigProvider,
  ) {
    val dbConfig: DatabaseConfig[JdbcProfile] =
      dbConfigProvider.get[JdbcProfile]

    import dbConfig._
    import profile.api._

    class DiskGolfTrackTable(tag: Tag)
        extends Table[DiskGolfTrackRow](tag, "disk_golf_track") {
      def uuid: Rep[UUID] = column[UUID]("uuid", O.PrimaryKey)
      def ownerId: Rep[Long] = column[Long]("owner_id")
      def name: Rep[String] = column[String]("name")
      def timezone: Rep[String] = column[String]("timezone")

      def * : ProvenShape[DiskGolfTrackRow] =
        (
          uuid,
          ownerId,
          name,
          timezone,
        ) <> ((DiskGolfTrackRow.apply _).tupled, DiskGolfTrackRow.unapply)
    }

    object DiskGolfTrackQuery
        extends TableQuery[DiskGolfTrackTable](new DiskGolfTrackTable(_))

  }

  case class DiskGolfTrackRow(
      id: UUID,
      ownerId: Long,
      name: String,
      timezone: String,
  )

  def fromDomain(diskGolfTrack: DiskGolfTrack): DiskGolfTrackRow =
    DiskGolfTrackRow(
      diskGolfTrack.uuid.value,
      diskGolfTrack.ownerId.value,
      diskGolfTrack.name,
      diskGolfTrack.timezone.toString,
    )

  def toDomain(diskGolfTrack: DiskGolfTrackRow): DiskGolfTrack =
    DiskGolfTrack(
      DiskGolfTrackUUID(diskGolfTrack.id),
      UserId(diskGolfTrack.ownerId),
      diskGolfTrack.name,
      TimeZone.getTimeZone(diskGolfTrack.timezone),
    )
}
