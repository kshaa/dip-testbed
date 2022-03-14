package diptestbed.database.services

import scala.concurrent.ExecutionContext
import slick.dbio.DBIOAction.sequenceOption
import cats.effect.Async
import cats.implicits._
import diptestbed.database.catalog.SoftwareCatalog.SoftwareRow
import diptestbed.domain.{HashedPassword, User, UserId}
import diptestbed.database.catalog.UserCatalog.{UserRow, UserTable, toDomain => userToDomain}
import diptestbed.database.driver.DatabaseDriverOps._
import diptestbed.database.driver.DatabaseOutcome.DatabaseResult

class UserService[F[_]: Async](
  val userTable: UserTable,
)(implicit executionContext: ExecutionContext) {
  import userTable.dbDriver.profile.api._
  import userTable._

  def countUsers(): F[DatabaseResult[Int]] =
    UserQuery.length.result.tryRunDBIO(dbDriver)

  def createUser(
    username: String,
    hashedPassword: HashedPassword,
    isManager: Boolean,
    isLabOwner: Boolean,
    isDeveloper: Boolean
  ): F[DatabaseResult[Option[User]]] = {
    val row: UserRow = UserRow(
      username = username,
      hashedPassword = hashedPassword.toSerializedString,
      isManager = isManager,
      isLabOwner = isLabOwner,
      isDeveloper = isDeveloper
    )
    val userCreation: DBIOAction[Option[Int], NoStream, Effect.Read with Effect.Write] = for {
      userUniqueCheck <- UserQuery.filter(_.username === username).result.headOption
      userCreation <- sequenceOption(Option.when(userUniqueCheck.isEmpty)(UserQuery += row))
    } yield userCreation

    userCreation
      .tryRunDBIO(dbDriver)
      .map(dbioAction => dbioAction.map(userId => userId.map(_ => userToDomain(row))))
  }

  def accessibleUserQuery(requester: Option[User]): Query[userTable.UserTable, UserRow, Seq] =
    requester match {
      // If no requester, then assuming full accessibility
      case None => UserQuery
      case Some(user) if user.isManager || user.isLabOwner => UserQuery
      case Some(user) => UserQuery.filter(s => s.uuid === user.id.value)
    }

  def getUsers(requester: Option[User]): F[DatabaseResult[Seq[User]]] =
    accessibleUserQuery(requester)
      .result
      .map(_.map(userToDomain))
      .tryRunDBIO(dbDriver)

  def getUser(requester: Option[User], id: UserId): F[DatabaseResult[Option[User]]] =
    accessibleUserQuery(requester)
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

  def getUserWithPassword(username: String, password: String): F[DatabaseResult[Option[User]]] =
    UserQuery
      .filter(_.username === username)
      .result
      .headOption
      .map(_.flatMap(row => {
        val user = userToDomain(row)
        val hashedPassword = HashedPassword.fromSerializedString(row.hashedPassword).get
        val supposedPassword = HashedPassword.fromPassword(password, hashedPassword.salt)
        Option.when(hashedPassword == supposedPassword)(user)
      }))
      .tryRunDBIO(dbDriver)

  def setPermissions(
    userId: UserId,
    isManager: Boolean,
    isLabOwner: Boolean,
    isDeveloper: Boolean
  ): F[DatabaseResult[Int]] =
    UserQuery
      .filter(_.uuid === userId.value)
      .map(u => (u.isManager, u.isLabOwner, u.isDeveloper))
      .update((isManager, isLabOwner, isDeveloper))
      .tryRunDBIO(dbDriver)

}
