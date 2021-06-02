package iotfrisbee.database.catalog

import iotfrisbee.database.driver.DatabaseDriver.JdbcDatabaseDriver
import iotfrisbee.domain.{DiskGolfDisk, DiskGolfDiskId, DiskGolfTrackId, HardwareId}
import slick.lifted.ProvenShape

import java.util.UUID

object DiskGolfDiskCatalog {
  class DiskGolfDiskTable(val dbDriver: JdbcDatabaseDriver) {

    import dbDriver.profile.api._

    class DiskGolfDiskTable(tag: Tag) extends Table[DiskGolfDiskRow](tag, "disk_golf_disk") {
      def uuid: Rep[UUID] = column[UUID]("uuid", O.PrimaryKey)
      def name: Rep[String] = column[String]("name")
      def trackUUID: Rep[UUID] = column[UUID]("track_uuid")
      def hardwareUUID: Rep[Option[UUID]] = column[Option[UUID]]("hardware_uuid")

      def * : ProvenShape[DiskGolfDiskRow] =
        (
          uuid,
          name,
          trackUUID,
          hardwareUUID,
        ) <> ((DiskGolfDiskRow.apply _).tupled, DiskGolfDiskRow.unapply)
    }

    object DiskGolfDiskQuery extends TableQuery[DiskGolfDiskTable](new DiskGolfDiskTable(_))
  }

  case class DiskGolfDiskRow(
    id: UUID = UUID.randomUUID(),
    name: String,
    trackUUID: UUID,
    hardwareUUID: Option[UUID],
  )

  def fromDomain(diskGolfDisk: DiskGolfDisk): DiskGolfDiskRow =
    DiskGolfDiskRow(
      diskGolfDisk.id.value,
      diskGolfDisk.name,
      diskGolfDisk.trackId.value,
      diskGolfDisk.hardwareId.map(_.value),
    )

  def toDomain(diskGolfDisk: DiskGolfDiskRow): DiskGolfDisk =
    DiskGolfDisk(
      DiskGolfDiskId(diskGolfDisk.id),
      diskGolfDisk.name,
      DiskGolfTrackId(diskGolfDisk.trackUUID),
      diskGolfDisk.hardwareUUID.map(HardwareId),
    )
}
