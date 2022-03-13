package diptestbed.web.control

import cats.effect.IO
import cats.effect.unsafe.IORuntime
import cats.implicits.toTraverseOps
import diptestbed.database.services.{SoftwareService, UserService}
import diptestbed.domain.DIPTestbedConfig
import diptestbed.web.ioControls.IOController
import play.api.mvc._

class AppUserController(
  val appConfig: DIPTestbedConfig,
  val cc: ControllerComponents,
  val userService: UserService[IO]
)(implicit
  iort: IORuntime
) extends AbstractController(cc)
    with IOController
    with ResultsController[IO]
    with AuthController[IO] {
  
  def list: Action[AnyContent] =
    Action { implicit request =>
      val userList = userService.getUsers.map(_.toOption.sequence.flatten.toList)
      Ok(diptestbed.web.views.html.userList(
        appConfig, contextUser.unsafeRunSync(), userList.unsafeRunSync()))
    }
}
