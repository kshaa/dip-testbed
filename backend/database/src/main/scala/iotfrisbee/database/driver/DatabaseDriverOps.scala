package iotfrisbee.database.driver

import cats.effect.kernel.Async
import iotfrisbee.database.driver.DatabaseOutcome.DatabaseResult
import slick.sql.SqlProfile
import slick.dbio.{DBIOAction, NoStream}
import scala.language.implicitConversions
import cats.implicits._
import slick.relational.RelationalBackend

object DatabaseDriverOps {
  implicit class DBIOActionSyntax[R](val dbioAction: DBIOAction[R, NoStream, Nothing]) {
    implicit def runDBIO[B <: RelationalBackend#DatabaseDef, P <: SqlProfile, F[_]: Async](
      databaseDriver: DatabaseDriver[B, P],
    ): F[R] =
      databaseDriver.runDBIO[F, R](dbioAction)

    implicit def tryRunDBIO[B <: RelationalBackend#DatabaseDef, P <: SqlProfile, F[_]: Async](
      databaseDriver: DatabaseDriver[B, P],
    ): F[DatabaseResult[R]] =
      databaseDriver.tryRunDBIO[F, R](dbioAction)
  }

  implicit class ResultSyntax[R](val dbioAction: DatabaseResult[R]) {
    implicit def tryGet: R = dbioAction.leftMap(_.value).toTry.get
  }
}
