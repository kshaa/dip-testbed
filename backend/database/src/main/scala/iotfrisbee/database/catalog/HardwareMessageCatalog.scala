package iotfrisbee.database.catalog

import java.util.UUID
import slick.lifted.ProvenShape
import iotfrisbee.database.driver.DatabaseDriver.JdbcDatabaseDriver
import iotfrisbee.domain.{HardwareId, HardwareMessage, HardwareMessageId}

object HardwareMessageCatalog {

  class HardwareMessageTable(val dbDriver: JdbcDatabaseDriver) {

    import dbDriver.profile.api._

    class HardwareMessageTable(tag: Tag) extends Table[HardwareMessageRow](tag, "hardware_message") {
      def uuid: Rep[UUID] = column[UUID]("uuid", O.PrimaryKey)
      def hardwareUuid: Rep[UUID] = column[UUID]("hardware_uuid")
      def messageType: Rep[String] = column[String]("type")
      def message: Rep[String] = column[String]("message")

      def * : ProvenShape[HardwareMessageRow] =
        (
          uuid,
          hardwareUuid,
          messageType,
          message,
        ) <> ((HardwareMessageRow.apply _).tupled, HardwareMessageRow.unapply)
    }

    object HardwareMessageQuery extends TableQuery[HardwareMessageTable](new HardwareMessageTable(_))

  }

  case class HardwareMessageRow(
    id: UUID = UUID.randomUUID(),
    hardwareId: UUID,
    messageType: String,
    message: String,
  )

  def fromDomain(hardwareMessage: HardwareMessage): HardwareMessageRow =
    HardwareMessageRow(
      hardwareMessage.id.value,
      hardwareMessage.hardwareId.value,
      hardwareMessage.messageType,
      hardwareMessage.message,
    )

  def toDomain(hardwareMessage: HardwareMessageRow): HardwareMessage =
    HardwareMessage(
      HardwareMessageId(hardwareMessage.id),
      HardwareId(hardwareMessage.hardwareId),
      hardwareMessage.messageType,
      hardwareMessage.message,
    )
}
