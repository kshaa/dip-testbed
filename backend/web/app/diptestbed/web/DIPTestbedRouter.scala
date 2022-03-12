package diptestbed.web

import play.api.routing.Router.Routes
import play.api.routing.SimpleRouter

class DIPTestbedRouter(
  apiRouter: APIRouter,
  apiPrefix: String,
  assetsRouter: AssetsRouter,
  assetsPrefix: String,
  appRouter: AppRouter,
  appPrefix: String
) extends SimpleRouter {
  def routes: Routes =
    apiRouter.withPrefix(apiPrefix).routes
      .orElse(appRouter.withPrefix(appPrefix).routes)
      .orElse(assetsRouter.withPrefix(assetsPrefix).routes)
}
