package com.iotfrisbee.catalog

import com.google.inject.Inject
import com.iotfrisbee.{User, UserId}
import play.api.db.slick.DatabaseConfigProvider
import slick.basic.DatabaseConfig
import slick.jdbc.JdbcProfile
import slick.lifted.ProvenShape
import javax.inject.Singleton

object UserCatalog {
  @Singleton
  class UserTable @Inject() (dbConfigProvider: DatabaseConfigProvider) {
    val dbConfig: DatabaseConfig[JdbcProfile] =
      dbConfigProvider.get[JdbcProfile]
    import dbConfig._
    import profile.api._

    class UserTable(tag: Tag) extends Table[UserRow](tag, "user") {
      def id: Rep[Long] = column[Long]("id", O.PrimaryKey, O.AutoInc)
      def username: Rep[String] = column[String]("name")
      def * : ProvenShape[UserRow] =
        (id, username) <> ((UserRow.apply _).tupled, UserRow.unapply)
    }

    object UserQuery extends TableQuery[UserTable](new UserTable(_))
  }

  case class UserRow(id: Long, username: String)

  def fromDomain(user: User): UserRow =
    UserRow(user.id.value, user.username)

  def toDomain(user: UserRow): User =
    User(UserId(user.id), user.username)
}
