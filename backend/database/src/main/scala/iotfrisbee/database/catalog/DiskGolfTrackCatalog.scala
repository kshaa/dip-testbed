package iotfrisbee.database.catalog

import java.util.UUID
import iotfrisbee.database.driver.DatabaseDriver.JdbcDatabaseDriver
import iotfrisbee.domain.{DiskGolfTrack, DiskGolfTrackId, DomainTimeZoneId, UserId}
import slick.lifted.ProvenShape

object DiskGolfTrackCatalog {
  class DiskGolfTrackTable(val dbDriver: JdbcDatabaseDriver) {
    import dbDriver.profile.api._

    class DiskGolfTrackTable(tag: Tag) extends Table[DiskGolfTrackRow](tag, "disk_golf_track") {
      def uuid: Rep[UUID] = column[UUID]("uuid", O.PrimaryKey)
      def ownerId: Rep[UUID] = column[UUID]("owner_id")
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

    object DiskGolfTrackQuery extends TableQuery[DiskGolfTrackTable](new DiskGolfTrackTable(_))
  }

  case class DiskGolfTrackRow(
    id: UUID = UUID.randomUUID(),
    ownerId: UUID,
    name: String,
    timezone: String,
  )

  def fromDomain(diskGolfTrack: DiskGolfTrack): DiskGolfTrackRow =
    DiskGolfTrackRow(
      diskGolfTrack.id.value,
      diskGolfTrack.ownerId.value,
      diskGolfTrack.name,
      diskGolfTrack.timezoneId.value,
    )

  def toDomain(diskGolfTrack: DiskGolfTrackRow): DiskGolfTrack =
    DiskGolfTrack(
      DiskGolfTrackId(diskGolfTrack.id),
      UserId(diskGolfTrack.ownerId),
      diskGolfTrack.name,
      DomainTimeZoneId.fromString(diskGolfTrack.timezone).toOption.get,
    )
}
