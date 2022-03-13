package diptestbed.web.control

import cats.Monad
import cats.data.EitherT
import cats.effect.IO
import cats.effect.unsafe.IORuntime
import diptestbed.database.driver.DatabaseOutcome.{DatabaseException, DatabaseResult}
import diptestbed.database.services.UserService
import diptestbed.domain.{HashedPassword, User}
import diptestbed.protocol.WebResult.Failure
import diptestbed.web.ioControls.PipelineOps._
import diptestbed.web.ioControls.PipelineTypes.PipelineRes
import play.api.http.Status.UNAUTHORIZED
import cats.implicits._
import play.api.mvc.{Request, Result}
import play.mvc.Security
import java.util.Base64
import scala.io.Source
import scala.util.Try

trait AuthController[F[_]] { self: ResultsController[F] =>
  val effectMonad: Monad[F]
  val userService: UserService[F]

  val authorizationErrorResult: Result = Failure("Failed to authenticate request")
    .withHttpStatus(UNAUTHORIZED)
    .withHeaders("WWW-Authenticate" -> "Basic")

  def withRequestAuthn[R, H](request: Request[R])(handler: (Request[R], DatabaseResult[Option[User]]) => F[H]): F[H] = {
    implicit val implicitEffectMonad: Monad[F] = effectMonad

    AuthController
      .extractRequestUser(
        request,
        userService.getUserByName,
      )
      .flatMap(handler(request, _))
  }

  def withRequestAuthnOrFail[R](request: Request[R])(handler: (Request[R], User) => PipelineRes[F]): PipelineRes[F] = {
    implicit val implicitEffectMonad: Monad[F] = effectMonad

    EitherT(
      withRequestAuthn(request)((request: Request[R], userResult: DatabaseResult[Option[User]]) =>
        userResult
          .toEitherT[F]
          .leftMap(databaseErrorResult)
          .flatMap(_.toRight(authorizationErrorResult).toEitherT[F])
          .flatMap(handler(request, _))
          .value,
      ),
    )
  }

  def contextUser[R, H](implicit request: Request[R]): F[Option[User]] = {
    implicit val implicitEffectMonad: Monad[F] = effectMonad

    AuthController
      .extractRequestUser(
        request,
        userService.getUserByName,
      )
      .map(_.toOption.flatten)
  }
}

object AuthController {
  type Username = String
  type Password = String

  def extractRequestBasicAuth[R](request: Request[R]): Option[(Username, Password)] = {
    val auth = request.headers.get("Authorization")
    val authParts = auth.map(_.trim.split(" +").toList)
    val usernamePassword = authParts.flatMap {
      case "Basic" :: secret :: Nil =>
        Try(Base64.getDecoder.decode(secret)).toOption
          .map(bytes => Source.fromBytes(bytes, "UTF-8").mkString)
          .flatMap(_.split(":").toList match {
            case username :: password :: Nil => Some((username, password))
            case _                           => None
          })
      case _ => None
    }

    usernamePassword
  }

  def extractRequestUser[F[_]: Monad, E, R](
    request: Request[R],
    getUserByName: Username => F[DatabaseResult[Option[(User, HashedPassword)]]],
  ): F[DatabaseResult[Option[User]]] = {
    val sessionUserResult: F[DatabaseResult[Option[User]]] =
      request.session.get(Security.USERNAME.toString)
        .traverse(getUserByName(_))
        .map(_.getOrElse(Right(None)))
        .map(_.map(_.map { case (user, _) => user }))

    val basicAuthUserResult: F[DatabaseResult[Option[User]]] = extractRequestBasicAuth(request) match {
      case None => Right[DatabaseException, Option[User]](None).pure[F].widen
      case Some((username, password)) =>
        getUserByName(username).map(_.map(_.flatMap {
          case (user, hashedPassword) =>
            val hashedPasswordFromRequest = HashedPassword.fromPassword(password, hashedPassword.salt)
            Option.when(hashedPasswordFromRequest == hashedPassword)(user)
        }))
    }

    for {
      a <- sessionUserResult
      b <- basicAuthUserResult
      c = (a, b) match {
        // If session contains user, use it primarily
        case (Right(Some(u)), _) => Right(Some(u))
        // Else fallback to basic auth user
        case (_, Right(Some(u))) => Right(Some(u))
        // Otherwise return whatever else is left, doesn't matter much
        case (x, y) => x.orElse(y)
      }
    } yield c
  }

  def unsafeExtractRequestUser[E, R](
    request: Request[R],
    getUserByName: Username => IO[DatabaseResult[Option[(User, HashedPassword)]]],
  )(implicit iort: IORuntime): Option[User] =
    extractRequestUser(request, getUserByName).unsafeRunSync().toOption.flatten
}
