package diptestbed.database.catalog

import java.util.UUID
import slick.lifted.ProvenShape
import diptestbed.database.driver.DatabaseDriver.JdbcDatabaseDriver
import diptestbed.domain.{HashedPassword, User, UserId}

object UserCatalog {
  class UserTable(val dbDriver: JdbcDatabaseDriver) {
    import dbDriver.profile.api._

    class UserTable(tag: Tag) extends Table[UserRow](tag, "user") {
      def uuid: Rep[UUID] = column[UUID]("uuid", O.PrimaryKey)
      def username: Rep[String] = column[String]("username")
      def hashedPassword: Rep[String] = column[String]("hashed_password")

      def * : ProvenShape[UserRow] =
        (uuid, username, hashedPassword) <> ((UserRow.apply _).tupled, UserRow.unapply)
    }

    object UserQuery extends TableQuery[UserTable](new UserTable(_))
  }

  case class UserRow(id: UUID = UUID.randomUUID(), username: String, hashedPassword: String)

  def fromDomain(user: User, hashedPassword: HashedPassword): UserRow =
    UserRow(user.id.value, user.username, hashedPassword.toSerializedString)

  def toDomain(user: UserRow): User =
    User(UserId(user.id), user.username)
}
