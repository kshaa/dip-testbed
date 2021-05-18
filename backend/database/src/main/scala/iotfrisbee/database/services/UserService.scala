package iotfrisbee.database.services

import cats.effect.Async
import cats.implicits._
import iotfrisbee.domain.{User, UserId}
import iotfrisbee.database.catalog.UserCatalog.{UserRow, UserTable, toDomain => userToDomain}
import iotfrisbee.database.driver.DatabaseDriver.JdbcDatabaseDriver
import iotfrisbee.database.driver.DatabaseDriverOps._
import iotfrisbee.database.driver.DatabaseOutcome.DatabaseResult

import scala.concurrent.ExecutionContext

class UserService[F[_]: Async](
  val dbDriver: JdbcDatabaseDriver,
  val userTable: UserTable,
)(implicit executionContext: ExecutionContext) {
  import dbDriver.profile.api._
  import userTable._

  def getUserById(id: UserId): F[DatabaseResult[Option[User]]] =
    UserQuery
      .filter(_.id === id.value)
      .result
      .headOption
      .map(_.map(userToDomain))
      .tryRunDBIO(dbDriver)

  def countUsers(): F[DatabaseResult[Int]] =
    UserQuery.length.result.tryRunDBIO(dbDriver)

  def createUser(username: String): F[DatabaseResult[User]] = {
    val row = UserRow(0, username)

    (UserQuery += row)
      .tryRunDBIO(dbDriver)
      .map(_.map(rowId => userToDomain(row.copy(id = rowId))))
  }
}
