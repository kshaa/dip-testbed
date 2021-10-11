package iotfrisbee.database.services

import scala.concurrent.ExecutionContext
import slick.dbio.DBIOAction.sequenceOption
import cats.effect.Async
import cats.implicits._
import iotfrisbee.domain.{HashedPassword, User, UserId}
import iotfrisbee.database.catalog.UserCatalog.{UserRow, UserTable, toDomain => userToDomain}
import iotfrisbee.database.driver.DatabaseDriverOps._
import iotfrisbee.database.driver.DatabaseOutcome.DatabaseResult

class UserService[F[_]: Async](
  val userTable: UserTable,
)(implicit executionContext: ExecutionContext) {
  import userTable.dbDriver.profile.api._
  import userTable._

  def countUsers(): F[DatabaseResult[Int]] =
    UserQuery.length.result.tryRunDBIO(dbDriver)

  def createUser(username: String, hashedPassword: HashedPassword): F[DatabaseResult[Option[User]]] = {
    val row: UserRow = UserRow(username = username, hashedPassword = hashedPassword.toSerializedString)
    val userCreation: DBIOAction[Option[Int], NoStream, Effect.Read with Effect.Write] = for {
      userUniqueCheck <- UserQuery.filter(_.username === username).result.headOption
      userCreation <- sequenceOption(Option.when(userUniqueCheck.isEmpty)(UserQuery += row))
    } yield userCreation

    println(s"Creating user w/ hashedPassword: ${hashedPassword}")

    userCreation
      .tryRunDBIO(dbDriver)
      .map(dbioAction => dbioAction.map(userId => userId.map(_ => userToDomain(row))))
  }

  def getUsers: F[DatabaseResult[Seq[User]]] =
    UserQuery.result
      .map(_.map(userToDomain))
      .tryRunDBIO(dbDriver)

  def getUser(id: UserId): F[DatabaseResult[Option[User]]] =
    UserQuery
      .filter(_.uuid === id.value)
      .result
      .headOption
      .map(_.map(userToDomain))
      .tryRunDBIO(dbDriver)

  def getUserByName(username: String): F[DatabaseResult[Option[(User, HashedPassword)]]] =
    UserQuery
      .filter(_.username === username)
      .result
      .headOption
      .map(_.map(row => (userToDomain(row), HashedPassword.fromSerializedString(row.hashedPassword).get)))
      .tryRunDBIO(dbDriver)

}
