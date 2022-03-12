package diptestbed.web.control

import scala.annotation.unused
import scala.concurrent.ExecutionContext
import akka.stream.Materializer
import cats.data.EitherT
import cats.effect.IO
import cats.effect.unsafe.IORuntime
import cats.implicits._
import play.api.mvc._
import diptestbed.database.services.UserService
import diptestbed.domain.{HashedPassword, UserId}
import diptestbed.protocol._
import diptestbed.protocol.Codecs._
import diptestbed.protocol.WebResult._
import diptestbed.web.ioControls.PipelineOps._
import diptestbed.web.ioControls._

class ApiUserController(
  val cc: ControllerComponents,
  val userService: UserService[IO],
)(implicit
  @unused ec: ExecutionContext,
  @unused iort: IORuntime,
  @unused materializer: Materializer,
) extends AbstractController(cc)
    with IOController
    with ResultsController[IO] {

  def createUser: Action[CreateUser] = {
    IOActionJSON[CreateUser] { request =>
      EitherT(userService.createUser(request.body.username, HashedPassword.fromPassword(request.body.password)))
        .leftMap(databaseErrorResult)
        .subflatMap(
          _.toRight("Username already taken")
            .bimap(
              errorMessage => Failure(errorMessage).withHttpStatus(BAD_REQUEST),
              user => Success(user).withHttpStatus(OK),
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
