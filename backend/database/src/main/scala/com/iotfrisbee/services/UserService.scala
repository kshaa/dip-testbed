package com.iotfrisbee.services

import cats.effect.IO
import com.google.inject.Inject
import com.iotfrisbee.{User, UserId}
import com.iotfrisbee.catalog.UserCatalog.{UserTable, toDomain => userToDomain}
import play.api.db.slick.DatabaseConfigProvider
import slick.basic.DatabaseConfig
import slick.jdbc.JdbcProfile
import javax.inject.Singleton
import scala.concurrent.ExecutionContext.Implicits.global

@Singleton
class UserService @Inject() (
    dbConfigProvider: DatabaseConfigProvider,
    userTable: UserTable,
) {
  private val dbConfig: DatabaseConfig[JdbcProfile] =
    dbConfigProvider.get[JdbcProfile]
  import dbConfig._
  import profile.api._
  import userTable._

  def getUserById(id: UserId): IO[Option[User]] =
    IO.fromFuture(
      IO(
        db.run(
          UserQuery
            .filter(_.id === id.value)
            .result
            .headOption
            .map(_.map(userToDomain)),
        ),
      ),
    )

  def countUsers(): IO[Int] =
    IO.fromFuture(IO(db.run(UserQuery.length.result)))
}
