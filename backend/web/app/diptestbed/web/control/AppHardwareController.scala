package diptestbed.web.control

import cats.effect.IO
import cats.effect.unsafe.IORuntime
import cats.implicits.toTraverseOps
import diptestbed.database.services.{HardwareService, UserService}
import diptestbed.domain.DIPTestbedConfig
import diptestbed.web.ioControls.IOController
import play.api.mvc._

class AppHardwareController(
  val appConfig: DIPTestbedConfig,
  val cc: ControllerComponents,
  val hardwareService: HardwareService[IO],
  val userService: UserService[IO]
)(implicit
  iort: IORuntime
) extends AbstractController(cc)
    with IOController
    with ResultsController[IO]
    with AuthController[IO] {
  implicit val ac: DIPTestbedConfig = appConfig

  def list: Action[AnyContent] =
    Action { implicit request =>
      withRequestAuthnOrLoginRedirect[AnyContent] { case (_, user) =>
        val hardwareList = hardwareService.getHardwares(Some(user)).map(_.toOption.sequence.flatten.toList)
        Ok(diptestbed.web.views.html.hardwareList(
          appConfig, Some(user), hardwareList.unsafeRunSync()))
      }.unsafeRunSync()
    }
}
