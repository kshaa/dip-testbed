package iotfrisbee.web

import iotfrisbee.web.controllers.HomeController
import play.api.routing.Router.Routes
import play.api.routing.SimpleRouter
import play.api.routing.sird._

class IotFrisbeeRouter(
  homeController: HomeController,
) extends SimpleRouter {
  def routes: Routes = {
    case GET(p"/")                 => homeController.index
    case GET(p"/status")           => homeController.status
    case GET(p"/user/${username}") => homeController.addUser(username)
  }
}
