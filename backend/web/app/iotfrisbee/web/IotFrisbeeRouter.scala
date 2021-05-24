package iotfrisbee.web

import play.api.routing.Router.Routes
import play.api.routing.SimpleRouter
import play.api.routing.sird._
import iotfrisbee.web.controllers.{HomeController, UserController}
import iotfrisbee.web.sird.UUIDBinding.uuid

class IotFrisbeeRouter(
  homeController: HomeController,
  userController: UserController,
) extends SimpleRouter {
  def routes: Routes = {
    case GET(p"/")       => homeController.index
    case GET(p"/status") => homeController.status

    // Users
    case POST(p"/users")                => userController.createUser
    case GET(p"/users")                 => userController.getUsers
    case GET(p"/users/${uuid(userId)}") => userController.getUser(userId)
  }
}
