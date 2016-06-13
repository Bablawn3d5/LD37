// Copyright 2015-2016 Bablawn3d5

#include <boost/python.hpp>
#include <Farquaad/Serialization.hpp>
#include <json/json.h>
#include <SFML/Graphics.hpp>
#include <Box2D/Box2D.h>
#include <entityx/entityx.h>
#include <Farquaad/Systems.hpp>
#include <Farquaad/Components.hpp>
#include <Farquaad/Core.hpp>
#include <Farquaad/Thor/ResourceLoader.hpp>
#include <Farquaad/Box2D/SFMLB2DDebug.h>
#include <Thor/Resources.hpp>

#include <Farquaad/Systems/PythonSystem.h>
#include <string>

namespace fs = boost::filesystem;

// HACK(SMA) : Just shove this here for now.
BOOST_PYTHON_MODULE(_entityx_components) {
  Serializable::initPy<Body>(py::class_<Body>("Body", py::init<>()));
  Serializable::initPy<Physics>(py::class_<Physics>("Physics", py::init<>()));
  Serializable::initPy<Stats>(py::class_<Stats>("Stats", py::init<>()));
  Serializable::initPy<InputResponder>(
    py::class_<InputResponder>("InputResponder", py::init<>()));
  Serializable::initPy<std::vector<std::string>>(
    py::class_<std::vector<std::string>>("std_vector_string", py::init<>()));

  // This doesn't work
  //Serializable::initPy<sf::Vector2i>(
  //  py::class_<sf::Vector2i>("sf_vector_int", py::init<>()));

  // TODO(SMA) : Seralize me 
  py::class_< sf::Vector2<int> >("Vec2i", py::init<>())
    .def_readwrite("x", &sf::Vector2<int>::x)
    .def_readwrite("y", &sf::Vector2<int>::y);

  py::class_< sf::Vector2<float> >("Vec2f", py::init<>())
    .def_readwrite("x", &sf::Vector2<float>::x)
    .def_readwrite("y", &sf::Vector2<float>::y);
}

// Quick test for EntityX
class Application : public entityx::EntityX {
public:
    std::shared_ptr<b2World> physWorld;
    std::shared_ptr<SFMLB2DDebug> debugDraw;

    explicit Application(sf::RenderWindow &target, Json::Value& v) { // NOLINT
        b2Vec2 gravity = b2Vec2(0.0f, 0.0f);
        physWorld = std::make_shared<b2World>(gravity);
        debugDraw = std::make_shared<SFMLB2DDebug>(target);
        debugDraw->SetFlags(b2Draw::e_shapeBit | b2Draw::e_centerOfMassBit |
                            b2Draw::e_aabbBit | b2Draw::e_pairBit);

        systems.add<PhysicsSystem>(physWorld, debugDraw.get());
        auto inputSystem = systems.add<InputSystem>(target);
        inputSystem->setKeybinds(Serializable::fromJSON<InputSystem::KeyBindMap>(v["keys"]));

        systems.add<RenderSystem>(target);
        systems.add<MoveSystem>();
        systems.add<ImGuiSystem>(target);

        std::string path_exec = fs::current_path().string();
        std::string path_scripts = (fs::current_path() / "scripts").string();
        assert(
          PyImport_AppendInittab("_entityx_components", init_entityx_components) != -1
          && "Failed to initialize _entityx_components Python module");
#ifdef NDEBUG
        PyImport_AppendInittab("_entityx_components", init_entityx_components);
#endif
        auto pythonSystem = systems.add<PythonSystem>(&entities, path_exec.c_str());
        pythonSystem->add_path(path_scripts.c_str());
        systems.configure();

        // HACK(SMA) : Create entity right in this bloated constructor.
        thor::ResourceHolder<Json::Value, std::string> holder;
        for ( auto items : v["entities"] ) {
            std::cout << "Loading file: " << items.asString() << std::endl;
            auto json = holder.acquire(items.asString(),
                                       Resources::loadJSON(items.asString()));
            EntitySerializer es(json);
            auto entity = entities.create();
            es.Load(entity);
        }

        // HACK(SMA) : Create 'background' right up in here.
        {
            std::unique_ptr<sf::CircleShape> shape(new sf::CircleShape(100.f));
            shape->setFillColor(sf::Color::Green);

            auto entity = entities.create();
            entity.assign<Body>();
            entity.assign<RenderableShape>(std::move(shape));
        }
    }

    ~Application() {
    }

    void update(ex::TimeDelta dt) {
        systems.update<InputSystem>(dt);
        systems.update<MoveSystem>(dt);
        systems.update<PythonSystem>(dt);
        systems.update<PhysicsSystem>(dt);
        systems.update<RenderSystem>(dt);
        systems.update<ImGuiSystem>(dt);
        physWorld->DrawDebugData();
    }
};

int main() {
    sf::RenderWindow window(sf::VideoMode(800, 600), "");
    window.setKeyRepeatEnabled(false);

    // HACK(SMA) : Initalize these component serializers so they become registered.
    // FIXME(SMA) : These cause JSON objects to be held in memory permanantly. FIXME.
    {
        Serializable::handle<Body>();
        Serializable::handle<Stats>();
        Serializable::handle<Physics>();
        Serializable::handle<PythonScript>();
        Serializable::handle<InputResponder>();
    }

    thor::ResourceHolder<Json::Value, std::string> holder;
    Json::Value configs = holder.acquire("config", Resources::loadJSON("Config.json"));
    const std::string title = configs["app_title"].asString();

    Application app(window, configs);

    sf::Clock clock;
    while ( window.isOpen() ) {
      window.clear();
      sf::Time elapsed = clock.restart();
      app.update(elapsed.asSeconds());
      window.display();
    }

    return 0;
}
