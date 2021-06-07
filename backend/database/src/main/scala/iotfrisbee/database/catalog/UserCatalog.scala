package iotfrisbee.database.catalog

import java.util.UUID
import slick.lifted.ProvenShape
import iotfrisbee.database.driver.DatabaseDriver.JdbcDatabaseDriver
import iotfrisbee.domain.{User, UserId}

object UserCatalog {
  class UserTable(val dbDriver: JdbcDatabaseDriver) {
    import dbDriver.profile.api._

    class UserTable(tag: Tag) extends Table[UserRow](tag, "user") {
      def uuid: Rep[UUID] = column[UUID]("uuid", O.PrimaryKey)
      def username: Rep[String] = column[String]("username")
      def * : ProvenShape[UserRow] =
        (uuid, username) <> ((UserRow.apply _).tupled, UserRow.unapply)
    }

    object UserQuery extends TableQuery[UserTable](new UserTable(_))
  }

  case class UserRow(id: UUID = UUID.randomUUID(), username: String)

  def fromDomain(user: User): UserRow =
    UserRow(user.id.value, user.username)

  def toDomain(user: UserRow): User =
    User(UserId(user.id), user.username)
}
