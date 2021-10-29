package diptestbed.database.driver

import cats.effect.kernel.Async
import slick.basic.DatabaseConfig
import slick.jdbc.{H2Profile, JdbcBackend, JdbcProfile}
import slick.sql.SqlProfile
import cats.implicits._
import diptestbed.database.driver.DatabaseOutcome.{DatabaseException, DatabaseResult}
import slick.relational.RelationalBackend
import play.api.db.{Database => PlayDatabase}
import slick.dbio.{DBIOAction, Effect, NoStream}
import slick.jdbc.JdbcBackend.{Database => SlickDatabase}

import scala.concurrent.ExecutionContext

trait DatabaseDriver[B <: RelationalBackend#DatabaseDef, P <: SqlProfile] {
  val database: B
  val profile: P

  def runDBIO[F[_]: Async, R](dbioAction: DBIOAction[R, NoStream, Nothing]): F[R] =
    Async[F].fromFuture(Async[F].pure(database.run(dbioAction)))

  def tryRunDBIO[F[_]: Async, R](dbioAction: DBIOAction[R, NoStream, Nothing]): F[DatabaseResult[R]] =
    runDBIO(dbioAction).map(Either.catchNonFatal(_).leftMap(DatabaseException))
}

object DatabaseDriver {
  type JdbcDatabaseDriver = DatabaseDriver[JdbcBackend#DatabaseDef, JdbcProfile]

  def fromJdbcConfig(config: DatabaseConfig[JdbcProfile]): JdbcDatabaseDriver =
    new DatabaseDriver[JdbcBackend#DatabaseDef, JdbcProfile] {
      val database: JdbcBackend#DatabaseDef = config.db
      val profile: JdbcProfile = config.profile
    }

  def fromPlayDatabase(
    config: PlayDatabase,
    jdbcProfile: JdbcProfile,
    maxConnections: Option[Int] = None,
  ): JdbcDatabaseDriver =
    new DatabaseDriver[JdbcBackend#DatabaseDef, JdbcProfile] {
      val database: JdbcBackend#DatabaseDef = SlickDatabase.forDataSource(config.dataSource, maxConnections)
      val profile: JdbcProfile = jdbcProfile
    }

  def fromSlickH2Url(h2Url: String, h2Driver: String): JdbcDatabaseDriver =
    new DatabaseDriver[JdbcBackend#DatabaseDef, JdbcProfile] {
      val profile: JdbcProfile = H2Profile
      val database: JdbcBackend#DatabaseDef =
        SlickDatabase.forURL(h2Url, driver = h2Driver)
    }

  def existsOrError[A, B](action: DBIOAction[Option[A], NoStream, Effect.Read], error: B)(implicit
    ec: ExecutionContext,
  ): DBIOAction[Option[B], NoStream, Effect.Read] =
    action.map(_.fold[Option[B]](Some(error))(_ => None))

}
