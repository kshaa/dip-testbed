package diptestbed.web

import diptestbed.web.control.AppHomeController
import play.api.routing.Router.Routes
import play.api.routing.SimpleRouter
import play.api.routing.sird._

class RedirectRouter(
  appHomeController: AppHomeController
) extends SimpleRouter {
  def routes: Routes = {
    case GET(p"/") => appHomeController.redirect("/app")
  }
}
