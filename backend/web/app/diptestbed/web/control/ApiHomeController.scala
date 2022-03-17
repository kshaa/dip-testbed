package diptestbed.web.control

import scala.annotation.unused
import scala.concurrent.ExecutionContext
import akka.stream.Materializer
import cats.data.EitherT
import cats.effect.unsafe.IORuntime
import cats.effect.IO
import play.api.mvc._
import diptestbed.database.services._
import diptestbed.domain.DIPTestbedConfig
import diptestbed.web.ioControls.PipelineOps._
import diptestbed.web.ioControls._
import diptestbed.protocol.{Hello, ServiceStatus}
import diptestbed.protocol.WebResult._
import diptestbed.protocol.DomainCodecs._

class ApiHomeController(
  val appConfig: DIPTestbedConfig,
  val cc: ControllerComponents,
  val userService: UserService[IO],
  val hardwareService: HardwareService[IO],
  val softwareService: SoftwareService[IO],
)(implicit
  @unused ec: ExecutionContext,
  @unused iort: IORuntime,
  @unused materializer: Materializer,
) extends AbstractController(cc)
    with IOController
    with ResultsController[IO]
    with AuthController[IO] {

  def index: Action[AnyContent] =
    IOActionAny(withRequestAuthnOrFail(_)((_, _) =>
      EitherT.liftF(IO.pure(Success(Hello("diptestbed")).withHttpStatus(OK)))
    ))

  def status: Action[AnyContent] =
    IOActionAny { _ =>
      (for {
        userCount <- EitherT(userService.countUsers())
        hardwareCount <- EitherT(hardwareService.countAllHardware())
        softwareCount <- EitherT(softwareService.countAllSoftware())
        status = ServiceStatus(
          userCount,
          hardwareCount,
          softwareCount,
        )
      } yield status)
        .bimap(
          error => Failure[String](error.message).withHttpStatus(INTERNAL_SERVER_ERROR),
          status => Success(status).withHttpStatus(OK),
        )
    }

  def authCheck: Action[AnyContent] =
    IOActionAny(withRequestAuthnOrFail(_)((_, user) =>
      EitherT.liftF(IO.pure(Success(user).withHttpStatus(OK)))
    ))

}
