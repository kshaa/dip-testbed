package diptestbed.web.control

import cats.effect.IO
import cats.effect.unsafe.IORuntime
import diptestbed.database.services.UserService
import diptestbed.domain.DIPTestbedConfig
import diptestbed.web.ioControls.IOController
import play.api.mvc._

class AppHomeController(
  val appConfig: DIPTestbedConfig,
  val cc: ControllerComponents,
  val userService: UserService[IO]
)(implicit
  iort: IORuntime
) extends AbstractController(cc)
    with IOController
    with ResultsController[IO]
    with AuthController[IO] {

  def index: Action[AnyContent] =
    Action { implicit request =>
      Ok(diptestbed.web.views.html.index(appConfig, contextUser.unsafeRunSync()))
    }

  def redirect(path: String): Action[AnyContent] = Action(Redirect(path))
}
