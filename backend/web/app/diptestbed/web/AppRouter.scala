package diptestbed.web

import controllers.Assets
import diptestbed.web.control.AppHomeController
import play.api.routing.Router.Routes
import play.api.routing.SimpleRouter
import play.api.routing.sird._

class AppRouter(
  assets: Assets,
  homeController: AppHomeController,
) extends SimpleRouter {
  def routes: Routes = {
    case GET(p"/")       => homeController.index
    case GET(p"/assets/${asset}") => assets.at(asset)
  }
}
