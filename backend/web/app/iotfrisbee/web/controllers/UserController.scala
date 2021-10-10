package iotfrisbee.web.controllers

import scala.annotation.unused
import scala.concurrent.ExecutionContext
import akka.stream.Materializer
import cats.data.EitherT
import cats.effect.IO
import cats.effect.unsafe.IORuntime
import cats.implicits._
import play.api.mvc._
import iotfrisbee.database.services.UserService
import iotfrisbee.domain.{HashedPassword, UserId}
import iotfrisbee.protocol._
import iotfrisbee.protocol.Codecs._
import iotfrisbee.protocol.WebResult._
import iotfrisbee.web.ioControls.PipelineOps._
import iotfrisbee.web.ioControls._

class UserController(
  val cc: ControllerComponents,
  val userService: UserService[IO],
)(implicit
  @unused ec: ExecutionContext,
  @unused iort: IORuntime,
  @unused materializer: Materializer,
) extends AbstractController(cc)
    with IOController {

  def createUser: Action[CreateUser] = {
    IOActionJSON[CreateUser] { request =>
      EitherT(userService.createUser(request.body.username, HashedPassword.fromPassword(request.body.password)))
        .leftMap(error => Failure(error.message).withHttpStatus(INTERNAL_SERVER_ERROR))
        .flatMap(creation =>
          EitherT.fromEither(
            creation
              .toRight("Username already taken")
              .bimap(
                errorMessage => Failure(errorMessage).withHttpStatus(BAD_REQUEST),
                user => Success(user).withHttpStatus(OK),
              ),
          ),
        )
    }
  }

  def getUsers: Action[AnyContent] =
    IOActionAny { _ =>
      EitherT(userService.getUsers)
        .bimap(
          error => Failure(error.message).withHttpStatus(INTERNAL_SERVER_ERROR),
          users => Success(users).withHttpStatus(OK),
        )
    }

  def getUser(userId: UserId): Action[AnyContent] =
    IOActionAny { _ =>
      EitherT(userService.getUser(userId))
        .leftMap(error => Failure(error.message).withHttpStatus(INTERNAL_SERVER_ERROR))
        .flatMap(get =>
          EitherT.fromEither(
            get
              .toRight("User with that id doesn't exist")
              .bimap(
                errorMessage => Failure(errorMessage).withHttpStatus(BAD_REQUEST),
                user => Success(user).withHttpStatus(OK),
              ),
          ),
        )
    }
}
