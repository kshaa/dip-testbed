package diptestbed.web.control

import cats.Monad
import cats.data.EitherT
import cats.effect.IO
import cats.effect.unsafe.IORuntime
import diptestbed.database.driver.DatabaseOutcome.{DatabaseException, DatabaseResult}
import diptestbed.database.services.UserService
import diptestbed.domain.{DIPTestbedConfig, HashedPassword, User}
import diptestbed.protocol.WebResult.Failure
import diptestbed.web.ioControls.PipelineOps._
import diptestbed.web.ioControls.PipelineTypes.PipelineRes
import play.api.http.Status.UNAUTHORIZED
import cats.implicits._
import play.api.mvc.Results.Redirect
import play.api.mvc.{Request, Result}
import play.mvc.Security
import java.util.Base64
import scala.io.Source
import scala.util.Try

trait AuthController[F[_]] { self: ResultsController[F] =>
  val effectMonad: Monad[F]
  val userService: UserService[F]
  val appConfig: DIPTestbedConfig

  val authorizationErrorResult: Result = Failure("Failed to authenticate request")
    .withHttpStatus(UNAUTHORIZED)
    .withHeaders("WWW-Authenticate" -> "Basic")

  def withRequestAuthn[R, H](request: Request[R])(handler: (Request[R], DatabaseResult[Option[User]]) => F[H]): F[H] = {
    implicit val implicitEffectMonad: Monad[F] = effectMonad

    AuthController
      .extractRequestUser(
        request,
        userService.getUserByName,
        appConfig
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
        appConfig
      )
      .map(_.toOption.flatten)
  }

  def withRequestAuthnOrLoginRedirect[R](
    handler: (Request[R], User) => Result
  )(implicit request: Request[R], appConfig: DIPTestbedConfig): F[Result] = {
    implicit val implicitEffectMonad: Monad[F] = effectMonad

    contextUser.map {
      case None => Redirect(appConfig.withAppPath("/login"))
      case Some(user) => handler(request, user)
    }
  }
}

object AuthController {
  type Username = String
  type Password = String

  def validateLogin[F[_]: Monad](
    username: String,
    password: String,
    userService: UserService[F],
    config: DIPTestbedConfig
  ): F[DatabaseResult[Option[User]]] = {
    val adminUser = for {
      adminUsername <- config.adminUsername
      adminPassword <- config.adminPassword
      adminUser <-
        config.adminUser if username == adminUsername && password == adminPassword && config.adminEnabled
    } yield adminUser
    val gottenUser = userService.getUserWithPassword(username, password)
    adminUser match {
      case Some(user) => implicitly[Monad[F]].pure(Right(Some(user)))
      case None => gottenUser
    }
  }

  def validateRegistration[F[_]: Monad](
    username: String,
    password: String,
    userService: UserService[F],
    config: DIPTestbedConfig
  ): F[DatabaseResult[Option[User]]] = {
      val overridesAdmin = config.adminUsername.contains(username)
      if (overridesAdmin) implicitly[Monad[F]].pure(Right(None))
      else userService.createUser(username, HashedPassword.fromPassword(password))
  }

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
    config: DIPTestbedConfig
  ): F[DatabaseResult[Option[User]]] = {
    val sessionUserResult: F[DatabaseResult[Option[User]]] = {
      val username = request.session.get(Security.USERNAME.toString)

      val adminUser = (username, config.adminUsername)
        .tupled
        .mapFilter { case (a, b) => config.adminUser.filter(_ => a == b && config.adminEnabled) }

      val gottenUser = username
        .traverse(getUserByName(_))
        .map(_.getOrElse(Right(None)))
        .map(_.map(_.map { case (user, _) => user }))

      adminUser match {
        case Some(user) => implicitly[Monad[F]].pure(Right(Some(user)))
        case None => gottenUser
      }
    }

    val basicAuthUserResult: F[DatabaseResult[Option[User]]] = extractRequestBasicAuth(request) match {
      case None => Right[DatabaseException, Option[User]](None).pure[F].widen
      case Some((username, password)) =>
        val adminUser = for {
          adminUsername <- config.adminUsername
          adminPassword <- config.adminPassword
          adminUser <-
            config.adminUser if username == adminUsername && password == adminPassword && config.adminEnabled
        } yield adminUser

        val gottenUser = getUserByName(username).map(_.map(_.flatMap {
          case (user, hashedPassword) =>
            val hashedPasswordFromRequest = HashedPassword.fromPassword(password, hashedPassword.salt)
            Option.when(hashedPasswordFromRequest == hashedPassword)(user)
        }))

        adminUser match {
          case Some(user) => implicitly[Monad[F]].pure(Right(Some(user)))
          case None => gottenUser
        }
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
}
