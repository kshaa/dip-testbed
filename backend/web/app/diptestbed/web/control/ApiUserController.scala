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
import diptestbed.domain.{DIPTestbedConfig, HashedPassword, UserId}
import diptestbed.protocol._
import diptestbed.protocol.WebResult._
import diptestbed.web.ioControls.PipelineOps._
import diptestbed.web.ioControls._
import diptestbed.protocol.DomainCodecs._

class ApiUserController(
  val appConfig: DIPTestbedConfig,
  val cc: ControllerComponents,
  val userService: UserService[IO],
)(implicit
  @unused ec: ExecutionContext,
  @unused iort: IORuntime,
  @unused materializer: Materializer,
) extends AbstractController(cc)
    with IOController
    with ResultsController[IO]
    with AuthController[IO] {

  def createUser: Action[CreateUser] = {
    IOActionJSON[CreateUser] { request =>
      EitherT(userService.createUser(
        request.body.username,
        HashedPassword.fromPassword(request.body.password),
        isManager = false,
        isLabOwner = false,
        isDeveloper = false))
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
    IOActionAny(withRequestAuthnOrFail(_)((_, user) =>
      for {
        _ <- EitherT.fromEither[IO](Either.cond(
          user.isManager, (), permissionErrorResult("User access")))
        result <- EitherT(userService.getUsers(Some(user)))
          .bimap(
            error => Failure(error.message).withHttpStatus(INTERNAL_SERVER_ERROR),
            users => Success(users).withHttpStatus(OK),
          )
      } yield result
    ))

  def getUser(userId: UserId): Action[AnyContent] =
    IOActionAny(withRequestAuthnOrFail(_)((_, user) =>
      for {
        searchedUser <- EitherT(userService.getUser(Some(user), userId)).leftMap(databaseErrorResult)
        existingUser <- EitherT.fromEither[IO](searchedUser.toRight(unknownIdErrorResult))
        _ <- EitherT.fromEither[IO](Either.cond(
          user.isManager, (), permissionErrorResult("User access")))
        result = Success(existingUser).withHttpStatus(OK)
      } yield result
    ))
}
