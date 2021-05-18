package iotfrisbee.database.catalog

import iotfrisbee.database.driver.DatabaseDriver.JdbcDatabaseDriver
import iotfrisbee.domain.{User, UserId}
import slick.lifted.ProvenShape

object UserCatalog {
  class UserTable(val dbDriver: JdbcDatabaseDriver) {
    import dbDriver.profile.api._

    class UserTable(tag: Tag) extends Table[UserRow](tag, "user") {
      def id: Rep[Long] = column[Long]("id", O.PrimaryKey, O.AutoInc)
      def username: Rep[String] = column[String]("username")
      def * : ProvenShape[UserRow] =
        (id, username) <> ((UserRow.apply _).tupled, UserRow.unapply)
    }

    object UserQuery extends TableQuery[UserTable](new UserTable(_))
  }

  case class UserRow(id: Long = 0, username: String)

  def fromDomain(user: User): UserRow =
    UserRow(user.id.value, user.username)

  def toDomain(user: UserRow): User =
    User(UserId(user.id), user.username)
}
