package diptestbed.web.control

import cats.effect.IO
import cats.effect.unsafe.IORuntime
import cats.implicits.toTraverseOps
import diptestbed.database.services.{HardwareService, SoftwareService, UserService}
import diptestbed.domain.DIPTestbedConfig
import diptestbed.web.ioControls.IOController
import play.api.mvc._

class AppSoftwareController(
  val appConfig: DIPTestbedConfig,
  val cc: ControllerComponents,
  val softwareService: SoftwareService[IO],
  val userService: UserService[IO]
)(implicit
  iort: IORuntime
) extends AbstractController(cc)
    with IOController
    with ResultsController[IO]
    with AuthController[IO] {
  
  def list: Action[AnyContent] =
    Action { implicit request =>
      val softwareList = softwareService.getSoftwareMetas.map(_.toOption.sequence.flatten.toList)
      Ok(diptestbed.web.views.html.softwareList(
        appConfig, contextUser.unsafeRunSync(), softwareList.unsafeRunSync()))
    }
}
