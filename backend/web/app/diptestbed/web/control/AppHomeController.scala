package diptestbed.web.control

import diptestbed.domain.DIPTestbedConfig
import play.api.mvc._

class AppHomeController(
  val appConfig: DIPTestbedConfig,
  val cc: ControllerComponents,
) extends AbstractController(cc) {

  def index: Action[AnyContent] =
    Action(Ok(diptestbed.web.views.html.index(appConfig)))

  def redirect(path: String): Action[AnyContent] = Action(Redirect(path))
}
