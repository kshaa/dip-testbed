package diptestbed.web

import diptestbed.web.controllers._
import play.api.routing.Router.Routes
import play.api.routing.SimpleRouter
import play.api.routing.sird._

class AppRouter(
  homeController: HomeController,
) extends SimpleRouter {
  def routes: Routes = {
    case GET(p"/")       => homeController.indexHTML
  }
}
