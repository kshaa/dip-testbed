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
    case POST(p"/users")                => userController.createUser
    case GET(p"/users")                 => userController.getUsers
    case GET(p"/users/${uuid(userId)}") => userController.getUser(UserId(userId))

    // Hardware
    case POST(p"/hardwares")                    => hardwareController.createHardware
    case GET(p"/hardwares")                     => hardwareController.getHardwares
    case GET(p"/hardwares/${uuid(hardwareId)}") => hardwareController.getHardware(HardwareId(hardwareId))

    // Hardware message
    case POST(p"/hardware-messages") => hardwareMessageController.createHardwareMessage
    case GET(p"/hardware-messages")  => hardwareMessageController.getHardwareMessages(None)
    case GET(p"/hardware-messages/${uuid(hardwareMessageId)}") =>
      hardwareMessageController.getHardwareMessage(HardwareMessageId(hardwareMessageId))
    case GET(p"/hardwares/${uuid(hardwareId)}/messages") =>
      hardwareMessageController.getHardwareMessages(Some(HardwareId(hardwareId)))
    case GET(p"/hardwares/${uuid(hardwareId)}/messages/subscribe") =>
      hardwareMessageController.subscribeHardwareMessages(HardwareId(hardwareId))

  }
}
