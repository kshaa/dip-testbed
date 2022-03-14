package diptestbed.database.catalog

import diptestbed.database.driver.DatabaseDriver.JdbcDatabaseDriver
import diptestbed.domain.{Hardware, HardwareAccess, HardwareId, UserId}
import slick.lifted.ProvenShape

import java.util.UUID

object HardwareAccessCatalog {
  class HardwareAccessTable(val dbDriver: JdbcDatabaseDriver) {
    import dbDriver.profile.api._

    class HardwareAccessTable(tag: Tag) extends Table[HardwareAccessRow](tag, "hardware_access") {
      def hardwareId: Rep[UUID] = column[UUID]("hardware_uuid")
      def userId: Rep[UUID] = column[UUID]("user_uuid")

      def * : ProvenShape[HardwareAccessRow] =
        (hardwareId, userId) <> ((HardwareAccessRow.apply _).tupled, HardwareAccessRow.unapply)
    }

    object HardwareAccessQuery extends TableQuery[HardwareAccessTable](new HardwareAccessTable(_))
  }

  case class HardwareAccessRow(hardwareId: UUID, userId: UUID)

  def fromDomain(access: HardwareAccess): HardwareAccessRow =
    HardwareAccessRow(
      access.hardwareId.value,
      access.userId.value
    )

  def toDomain(access: HardwareAccessRow): HardwareAccess =
    HardwareAccess(
      HardwareId(access.hardwareId),
      UserId(access.userId),
    )
}
