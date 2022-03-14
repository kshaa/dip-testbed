package diptestbed.database.catalog

import diptestbed.database.driver.DatabaseDriver.JdbcDatabaseDriver
import slick.lifted.ProvenShape
import java.util.UUID

object SoftwareCatalog {
  class SoftwareTable(val dbDriver: JdbcDatabaseDriver) {
    import dbDriver.profile.api._

    class SoftwareTable(tag: Tag) extends Table[SoftwareRow](tag, "software") {
      def uuid: Rep[UUID] = column[UUID]("uuid", O.PrimaryKey)
      def ownerUuid: Rep[UUID] = column[UUID]("owner_uuid")
      def name: Rep[String] = column[String]("name")
      def isPublic: Rep[Boolean] = column[Boolean]("is_public")
      def content: Rep[Array[Byte]] = column[Array[Byte]]("content")

      def * : ProvenShape[SoftwareRow] =
        (
          uuid, ownerUuid, name, isPublic, content
        ) <> ((SoftwareRow.apply _).tupled, SoftwareRow.unapply)
    }

    object SoftwareQuery extends TableQuery[SoftwareTable](new SoftwareTable(_))
  }

  case class SoftwareRow(
    id: UUID = UUID.randomUUID(),
    ownerId: UUID,
    name: String,
    isPublic: Boolean,
    content: Array[Byte])
}
