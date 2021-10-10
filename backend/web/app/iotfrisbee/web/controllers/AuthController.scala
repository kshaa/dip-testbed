package iotfrisbee.web.controllers

import cats.Monad
import cats.implicits._
import play.api.mvc._
import iotfrisbee.database.services.UserService
import iotfrisbee.domain.{HashedPassword, User}
import iotfrisbee.web.controllers.AuthController.Username
import java.util.Base64
import scala.io.Source
import scala.util.Try

trait AuthController[F[_]] {
  implicit def effectMonad: Monad[F]
  val userService: UserService[F]

  def withOptionRequestAuthnF[R, H](request: Request[R], handler: (Request[R], Option[User]) => F[H]): F[H] = {
    @annotation.nowarn
    def unsafeGetUserByName(username: Username): F[Option[(User, HashedPassword)]] =
      userService.getUserByName(username).map(x => x.right.get)
    AuthController.extractRequestUser(request,unsafeGetUserByName).flatMap(handler(request, _))
  }
}

object AuthController {
  type Username = String
  type Password = String

  def extractRequestBasicAuth[R](request: Request[R]): Option[(Username, Password)] = {
    val auth = request.headers.get("Authorization")
    val authParts = auth.map(_.trim.split(" +").toList)
    val hashedPassword = authParts.flatMap {
      case "Basic" :: secret :: Nil =>
        Try(Base64.getDecoder.decode(secret)).toOption
          .map(bytes => Source.fromBytes(bytes, "UTF-8").mkString)
          .flatMap(_.split(":").toList match {
            case username :: password :: Nil => Some((username, password))
            case _ => None
          })
      case _ => None
    }

    hashedPassword
  }

  def extractRequestUser[F[_]: Monad, R](
    request: Request[R],
    getUserByName: Username => F[Option[(User, HashedPassword)]]): F[Option[User]] = {
    val requestUsernameWithPassword = extractRequestBasicAuth(request)
    requestUsernameWithPassword.map { case (username: Username, password: Password) =>
      getUserByName(username).map(_.collect {
        case (user: User, hashedPassword: HashedPassword)
          if HashedPassword.fromPassword(password, hashedPassword.salt) == hashedPassword => user
      })
    }.sequence.map(_.flatten)
  }
}
