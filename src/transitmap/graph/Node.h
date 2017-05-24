// Copyright 2016, University of Freiburg,
// Chair of Algorithms and Data Structures.
// Authors: Patrick Brosi <brosi@informatik.uni-freiburg.de>

#ifndef TRANSITMAP_GRAPH_NODE_H_
#define TRANSITMAP_GRAPH_NODE_H_

#include <set>
#include "./OrderingConfiguration.h"
#include "./Route.h"
#include "gtfsparser/gtfs/Stop.h"
#include "pbutil/geo/Geo.h"
#include "pbutil/geo/PolyLine.h"

using namespace gtfsparser;
using namespace pbutil::geo;

namespace transitmapper {
namespace graph {

// forward declarations
class Edge;
class Node;
struct RouteOccurance;

// forward declaration of TransitGraph
class TransitGraph;

struct NodeFront {
  NodeFront(Edge* e, Node* n) : n(n), edge(e) {}

  Node* n;  // pointer to node here also

  Point getTripOccPos(const Route* r, const Configuration& c) const;
  Point getTripPos(const Edge* e, size_t pos, bool inv) const;

  Edge* edge;

  PolyLine geom;
  void setGeom(const PolyLine& g) { geom = g; };

  // TODO
  double refEtgLengthBefExp;
};

struct Partner {
  Partner(const NodeFront* f, const Edge* e, const Route* r)
      : front(f), edge(e), route(r){};
  const NodeFront* front;
  const Edge* edge;
  const Route* route;
};

struct InnerGeometry {
  InnerGeometry(PolyLine g, Partner a, Partner b, size_t slotF,
                size_t slotT)
      : geom(g), from(a), to(b), slotFrom(slotF), slotTo(slotT){};
  PolyLine geom;
  Partner from;
  Partner to;
  size_t slotFrom;
  size_t slotTo;
};

struct StationInfo {
  StationInfo(const std::string& id, const std::string& name)
      : id(id), name(name) {}
  std::string id, name;
};

class Node {
 public:
  Node(const std::string& id, Point pos);
  Node(const std::string& id, double x, double y);
  Node(const std::string& id, Point pos, StationInfo stop);
  Node(const std::string& id, double x, double y, StationInfo stop);

  ~Node();

  const std::vector<StationInfo>& getStops() const;
  void addStop(StationInfo s);
  const Point& getPos() const;
  void setPos(const Point& p);

  const std::string& getId() const;

  const std::set<Edge*>& getAdjListOut() const { return _adjListOut; }
  const std::set<Edge*>& getAdjListIn() const { return _adjListIn; }
  const std::vector<NodeFront>& getMainDirs() const { return _mainDirs; }
  std::vector<NodeFront>& getMainDirs() { return _mainDirs; }

  void addMainDir(NodeFront f);

  const NodeFront* getNodeFrontFor(const Edge* e) const;
  double getScore(const graph::Configuration& c) const;
  std::vector<Partner> getPartners(const NodeFront* f,
                                   const RouteOccurance& ro) const;

  std::vector<InnerGeometry> getInnerGeometries(const graph::Configuration& c,
                                                double prec) const;

  size_t getConnCardinality() const;

  Polygon getConvexFrontHull(double d, bool rectangulize) const;

  // add edge to this node's adjacency lists
  void addEdge(Edge* e);

  // get edge from or to this node, from or to node "other"
  Edge* getEdge(const Node* other) const;

  // remove edge from this node's adjacency lists
  void removeEdge(Edge* e);

  void addRouteConnException(const Route* r, const Edge* edgeA,
                             const Edge* edgeB);
  bool connOccurs(const Route* r, const Edge* edgeA, const Edge* edgeB) const;

  double getMaxNodeFrontWidth() const;
  size_t getMaxNodeFrontCardinality() const;

 private:
  std::string _id;
  std::set<Edge*> _adjListIn;
  std::set<Edge*> _adjListOut;
  Point _pos;

  std::vector<NodeFront> _mainDirs;

  std::vector<StationInfo> _stops;

  std::map<const Route*, std::map<const Edge*, std::set<const Edge*> > >
      _routeConnExceptions;

  size_t getNodeFrontPos(const NodeFront* a) const;

  InnerGeometry getInnerBezier(const Configuration& c,
                               const graph::Partner& partnerFrom,
                               const graph::Partner& partnerTo,
                               double prec) const;

  InnerGeometry getInnerStraightLine(const Configuration& c,
                                     const graph::Partner& partnerFrom,
                                     const graph::Partner& partnerTo) const;
  friend class TransitGraph;
};
}
}

#endif  // TRANSITMAP_GRAPH_NODE_H_
