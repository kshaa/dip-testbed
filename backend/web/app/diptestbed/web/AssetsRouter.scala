package diptestbed.web

import controllers.Assets
import play.api.routing.Router.Routes
import play.api.routing.SimpleRouter
import play.api.routing.sird._

class AssetsRouter(assets: Assets) extends SimpleRouter {
  def routes: Routes = {
    case GET(p"/${asset}") => assets.at(asset)
  }
}
