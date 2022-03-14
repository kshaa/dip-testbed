package diptestbed.web

import controllers.Assets
import diptestbed.web.control.{AppAuthController, AppHardwareController, AppHomeController, AppSoftwareController, AppUserController}
import play.api.routing.Router.Routes
import play.api.routing.SimpleRouter
import play.api.routing.sird._

class AppRouter(
  assets: Assets,
  homeController: AppHomeController,
  appAuthController: AppAuthController,
  appHardwareController: AppHardwareController,
  appSoftwareController: AppSoftwareController,
  appUserController: AppUserController
) extends SimpleRouter {
  def routes: Routes = {
    case GET(p"/") => homeController.index

    case GET(p"/assets/${asset}") => assets.at(asset)

    case GET(p"/login")     => appAuthController.login
    case POST(p"/login")    => appAuthController.loginRequest
    case GET(p"/register")  => appAuthController.register
    case POST(p"/register") => appAuthController.registerRequest
    case GET(p"/logout")    => appAuthController.logout

    case GET(p"/hardware")          => appHardwareController.list
    case GET(p"/software")          => appSoftwareController.list
    case GET(p"/user")              => appUserController.list
    case POST(p"/user/permissions") => appUserController.permissionsRequest
  }
}
