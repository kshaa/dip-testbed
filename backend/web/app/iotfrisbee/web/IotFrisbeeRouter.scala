package iotfrisbee.web

import play.api.routing.Router.Routes
import play.api.routing.SimpleRouter
import play.api.routing.sird._
import iotfrisbee.domain._
import iotfrisbee.web.controllers._
import iotfrisbee.web.sird.UUIDBinding.uuid

class IotFrisbeeRouter(
  homeController: HomeController,
  userController: UserController,
  hardwareController: HardwareController,
  hardwareMessageController: HardwareMessageController,
) extends SimpleRouter {
  def routes: Routes = {
    case GET(p"/")       => homeController.index
    case GET(p"/status") => homeController.status

    // Users
    case POST(p"/user")                => userController.createUser
    case GET(p"/user")                 => userController.getUsers
    case GET(p"/user/${uuid(userId)}") => userController.getUser(UserId(userId))

    // Hardware
    case POST(p"/hardware")                    => hardwareController.createHardware
    case GET(p"/hardware")                     => hardwareController.getHardwares
    case GET(p"/hardware/${uuid(hardwareId)}") => hardwareController.getHardware(HardwareId(hardwareId))

    // Hardware message
    case POST(p"/hardware-message") => hardwareMessageController.createHardwareMessage
    case GET(p"/hardware-message")  => hardwareMessageController.getHardwareMessages(None)
    case GET(p"/hardware-message/${uuid(hardwareMessageId)}") =>
      hardwareMessageController.getHardwareMessage(HardwareMessageId(hardwareMessageId))
    case GET(p"/hardware/${uuid(hardwareId)}/message") =>
      hardwareMessageController.getHardwareMessages(Some(HardwareId(hardwareId)))
    case GET(p"/hardware/${uuid(hardwareId)}/message/subscribe") =>
      hardwareMessageController.subscribeHardwareMessages(HardwareId(hardwareId))

  }
}
