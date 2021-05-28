package iotfrisbee.database.catalog

import java.util.UUID
import slick.lifted.ProvenShape
import iotfrisbee.database.driver.DatabaseDriver.JdbcDatabaseDriver
import iotfrisbee.domain.{DiskGolfTrack, DiskGolfTrackId, DomainTimeZoneId, UserId}

object DiskGolfTrackCatalog {
  class DiskGolfTrackTable(val dbDriver: JdbcDatabaseDriver) {
    import dbDriver.profile.api._

    class DiskGolfTrackTable(tag: Tag) extends Table[DiskGolfTrackRow](tag, "disk_golf_track") {
      def uuid: Rep[UUID] = column[UUID]("uuid", O.PrimaryKey)
      def ownerUuid: Rep[UUID] = column[UUID]("owner_uuid")
      def name: Rep[String] = column[String]("name")
      def timezone: Rep[String] = column[String]("timezone")

      def * : ProvenShape[DiskGolfTrackRow] =
        (
          uuid,
          ownerUuid,
          name,
          timezone,
        ) <> ((DiskGolfTrackRow.apply _).tupled, DiskGolfTrackRow.unapply)
    }

    object DiskGolfTrackQuery extends TableQuery[DiskGolfTrackTable](new DiskGolfTrackTable(_))
  }

  case class DiskGolfTrackRow(
    id: UUID = UUID.randomUUID(),
    ownerUUID: UUID,
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
      UserId(diskGolfTrack.ownerUUID),
      diskGolfTrack.name,
      DomainTimeZoneId.fromString(diskGolfTrack.timezone).toOption.get,
    )
}
