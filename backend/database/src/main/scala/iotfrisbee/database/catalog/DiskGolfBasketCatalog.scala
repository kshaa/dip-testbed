package iotfrisbee.database.catalog

import iotfrisbee.database.driver.DatabaseDriver.JdbcDatabaseDriver
import iotfrisbee.domain.{DiskGolfBasket, DiskGolfBasketId, DiskGolfTrackId, HardwareId}
import slick.lifted.ProvenShape

import java.util.UUID

object DiskGolfBasketCatalog {
  class DiskGolfBasketTable(val dbDriver: JdbcDatabaseDriver) {
    import dbDriver.profile.api._

    class DiskGolfBasketTable(tag: Tag) extends Table[DiskGolfBasketRow](tag, "disk_golf_basket") {
      def uuid: Rep[UUID] = column[UUID]("uuid", O.PrimaryKey)
      def trackUUID: Rep[UUID] = column[UUID]("track_uuid")
      def orderNumber: Rep[Int] = column[Int]("order_number")
      def name: Rep[String] = column[String]("name")
      def hardwareUUID: Rep[Option[UUID]] = column[Option[UUID]]("hardware_uuid")

      def * : ProvenShape[DiskGolfBasketRow] =
        (
          uuid,
          trackUUID,
          orderNumber,
          name,
          hardwareUUID,
        ) <> ((DiskGolfBasketRow.apply _).tupled, DiskGolfBasketRow.unapply)
    }

    object DiskGolfBasketQuery extends TableQuery[DiskGolfBasketTable](new DiskGolfBasketTable(_))
  }

  case class DiskGolfBasketRow(
    id: UUID = UUID.randomUUID(),
    trackUUID: UUID,
    orderNumber: Int,
    name: String,
    hardwareUUID: Option[UUID],
  )

  def fromDomain(diskGolfBasket: DiskGolfBasket): DiskGolfBasketRow =
    DiskGolfBasketRow(
      diskGolfBasket.id.value,
      diskGolfBasket.trackId.value,
      diskGolfBasket.orderNumber,
      diskGolfBasket.name,
      diskGolfBasket.hardwareId.map(_.value),
    )

  def toDomain(diskGolfBasket: DiskGolfBasketRow): DiskGolfBasket =
    DiskGolfBasket(
      DiskGolfBasketId(diskGolfBasket.id),
      DiskGolfTrackId(diskGolfBasket.trackUUID),
      diskGolfBasket.orderNumber,
      diskGolfBasket.name,
      diskGolfBasket.hardwareUUID.map(HardwareId),
    )
}
