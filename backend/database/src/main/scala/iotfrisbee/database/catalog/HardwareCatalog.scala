package iotfrisbee.database.catalog

import java.util.UUID
import slick.lifted.ProvenShape
import iotfrisbee.database.driver.DatabaseDriver.JdbcDatabaseDriver
import iotfrisbee.domain.{Hardware, HardwareId, UserId}

object HardwareCatalog {
  class HardwareTable(val dbDriver: JdbcDatabaseDriver) {
    import dbDriver.profile.api._

    class HardwareTable(tag: Tag) extends Table[HardwareRow](tag, "hardware") {
      def uuid: Rep[UUID] = column[UUID]("uuid", O.PrimaryKey)
      def name: Rep[String] = column[String]("name")
      def ownerUuid: Rep[UUID] = column[UUID]("owner_uuid")
      def batteryPercent: Rep[Double] = column[Double]("battery_percent")

      def * : ProvenShape[HardwareRow] =
        (
          uuid,
          name,
          batteryPercent,
          ownerUuid,
        ) <> ((HardwareRow.apply _).tupled, HardwareRow.unapply)
    }

    object HardwareQuery extends TableQuery[HardwareTable](new HardwareTable(_))
  }

  case class HardwareRow(
    id: UUID = UUID.randomUUID(),
    name: String,
    batteryPercent: Double = 0.00,
    ownerId: UUID,
  )

  def fromDomain(hardware: Hardware): HardwareRow =
    HardwareRow(
      hardware.id.value,
      hardware.name,
      hardware.batteryPercent,
      hardware.ownerId.value,
    )

  def toDomain(hardware: HardwareRow): Hardware =
    Hardware(
      HardwareId(hardware.id),
      hardware.name,
      hardware.batteryPercent,
      UserId(hardware.ownerId),
    )
}
