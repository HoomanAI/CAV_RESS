%% matlab_figures.m
% Generates MATLAB .fig files for all CAV Reliability paper figures.
% Run from the project root:  E:\Working Docs\Papers\Reliability CAV\
% Requires MATLAB R2019b or later. No additional toolboxes needed.
%
% Usage:
%   1. Open MATLAB
%   2. cd 'E:\Working Docs\Papers\Reliability CAV'
%   3. run('code\matlab_figures.m')
% All .fig files will appear in results\figures\matlab\

clear; clc; close all;

BASE    = 'E:\Working Docs\Papers\Reliability CAV';
TABLE_D = fullfile(BASE, 'results', 'tables');
OUT_D   = fullfile(BASE, 'results', 'figures', 'matlab');
if ~exist(OUT_D, 'dir'); mkdir(OUT_D); end

PHI_LEVELS = [1.00 0.95 0.90 0.85 0.80 0.75 0.70];
ALGOS      = {'QiGA','GA','PSO','ALNS','TS'};
COLORS_PHI = [0.08 0.40 0.75; 0.10 0.47 0.85; 0.26 0.65 0.96;
              1.00 0.60 0.00; 0.89 0.22 0.21];

% =========================================================================
%  Helper: pretty figure defaults
% =========================================================================
function set_defaults()
    set(0,'DefaultAxesFontSize',11,'DefaultAxesFontName','Arial');
    set(0,'DefaultLineLineWidth',2);
    set(0,'DefaultFigureColor','w');
end
set_defaults();

% =========================================================================
%  M1  SR / OTSR vs phi_min  (Exp 4)
% =========================================================================
fprintf('M1  SR vs phi_min...\n');
T4 = readtable(fullfile(TABLE_D,'exp4.csv'));
phi_u = sort(unique(T4.phi_min),'descend');

SR_mn   = arrayfun(@(p) mean(T4.SR(T4.phi_min==p)),   phi_u);
SR_sd   = arrayfun(@(p) std(T4.SR(T4.phi_min==p)),    phi_u);
OTSR_mn = arrayfun(@(p) mean(T4.OTSR(T4.phi_min==p)), phi_u);
OTSR_sd = arrayfun(@(p) std(T4.OTSR(T4.phi_min==p)),  phi_u);

fig = figure('Position',[100 100 800 480]);
hold on;
fill([phi_u; flipud(phi_u)],[SR_mn+SR_sd; flipud(SR_mn-SR_sd)],...
     [0.08 0.40 0.75],'FaceAlpha',0.15,'EdgeColor','none');
fill([phi_u; flipud(phi_u)],[OTSR_mn+OTSR_sd; flipud(OTSR_mn-OTSR_sd)],...
     [0.18 0.55 0.18],'FaceAlpha',0.15,'EdgeColor','none');
p1 = plot(phi_u, SR_mn,   'o-','Color',[0.08 0.40 0.75],'DisplayName','SR (%)');
p2 = plot(phi_u, OTSR_mn, 's--','Color',[0.18 0.55 0.18],'DisplayName','OTSR (%)');
xline(0.85,'--','Color',[1 0.6 0],'LineWidth',1.5,'Label','\phi^* = 0.85');
yline(85,':','Color',[0.5 0.5 0.5],'Label','85% target');
set(gca,'XDir','reverse');  xlabel('\phi_{min}');  ylabel('Service Rate (%)');
title('M1 — Service Quality Degradation vs. \phi_{min} (Exp 4)','FontWeight','bold');
legend([p1 p2],'Location','northwest');  ylim([0 105]);
grid on;  box off;
savefig(fig, fullfile(OUT_D,'M1_SR_vs_phi.fig'));
fprintf('   Saved M1_SR_vs_phi.fig\n');

% =========================================================================
%  M2  Algorithm RDI Comparison  (Exp 2)
% =========================================================================
fprintf('M2  Algorithm RDI...\n');
T2   = readtable(fullfile(TABLE_D,'exp2.csv'));
ns   = sort(unique(T2.n));
fig  = figure('Position',[100 100 900 500]);
hold on;

algo_colors = [0.13 0.59 0.95; 0.30 0.69 0.31;
               1.00 0.60 0.00; 0.96 0.26 0.21; 0.61 0.15 0.69];
nA   = numel(ALGOS);
nN   = numel(ns);
w    = 0.14;
x0   = 1:nN;

for ai = 1:nA
    rdi_v = zeros(1,nN);
    for ni = 1:nN
        n_val = ns(ni);
        seeds = unique(T2.seed(T2.n == n_val));
        rdi_seed = [];
        for si = 1:numel(seeds)
            g = T2(T2.n==n_val & T2.seed==seeds(si), :);
            z_min = min(g.Z); z_max = max(g.Z);
            denom = max(z_max - z_min, 1e-9);
            algo_row = g(strcmp(g.algo, ALGOS{ai}), :);
            if ~isempty(algo_row)
                rdi_seed(end+1) = abs(algo_row.Z(1) - z_min) / denom;
            end
        end
        rdi_v(ni) = mean(rdi_seed);
    end
    bar(x0 + (ai-3)*w, rdi_v, w, 'FaceColor', algo_colors(ai,:), ...
        'FaceAlpha', 0.82, 'DisplayName', ALGOS{ai});
end

set(gca,'XTick',x0,'XTickLabel',arrayfun(@(n)sprintf('n=%d',n),ns,'UniformOutput',false));
xlabel('Problem Size');  ylabel('RDI (lower = better)');
title('M2 — Algorithm RDI Comparison (\phi=1.0, Exp 2)','FontWeight','bold');
legend('Location','northeast','NumColumns',3);
grid on; box off;
savefig(fig, fullfile(OUT_D,'M2_Algorithm_RDI.fig'));
fprintf('   Saved M2_Algorithm_RDI.fig\n');

% =========================================================================
%  M3  3D SR Response Surface  (Exp 4 traffic)
% =========================================================================
fprintf('M3  3D SR surface...\n');
T4t   = readtable(fullfile(TABLE_D,'exp4_traffic.csv'));
phi_v = sort(unique(T4t.phi_min));
vc_v  = sort(unique(T4t.vc_bg));
[PHI_g, VC_g] = meshgrid(phi_v, vc_v);
SR_g  = zeros(numel(vc_v), numel(phi_v));
for pi = 1:numel(phi_v)
    for vi = 1:numel(vc_v)
        mask = T4t.phi_min == phi_v(pi) & T4t.vc_bg == vc_v(vi);
        if any(mask); SR_g(vi,pi) = mean(T4t.SR(mask)); end
    end
end

fig = figure('Position',[100 100 900 650]);
surf(PHI_g, VC_g*100, SR_g, SR_g, 'FaceAlpha',0.88,'EdgeColor',[0.5 0.5 0.5],'LineWidth',0.2);
colormap(flipud(autumn));  c = colorbar;  c.Label.String = 'SR (%)';
xlabel('\phi_{min}');  ylabel('Traffic Level (% Capacity)');  zlabel('SR (%)');
title('M3 — SR Response Surface: \phi_{min} \times Traffic','FontWeight','bold');
view(28, -55);  zlim([0 100]);  grid on;
% Floor contour
hold on;
contourf(PHI_g, VC_g*100, SR_g, [70 75 85 95 100], 'ShowText','off');
savefig(fig, fullfile(OUT_D,'M3_3D_SR_Surface.fig'));
fprintf('   Saved M3_3D_SR_Surface.fig\n');

% =========================================================================
%  M4  3D BPR Congestion Surface
% =========================================================================
fprintf('M4  BPR surface...\n');
phi_bpr = linspace(0.50, 1.00, 60);
vc_bpr  = linspace(0.00, 1.50, 60);
[PHI_b, VC_b] = meshgrid(phi_bpr, vc_bpr);
Z_bpr = min(1 + 0.15 * (VC_b ./ PHI_b).^4, 4.0);

fig = figure('Position',[100 100 900 650]);
surf(PHI_b, VC_b, Z_bpr, Z_bpr, 'FaceAlpha',0.90,'EdgeColor',[0.5 0.5 0.5],'LineWidth',0.2);
colormap(jet);  c = colorbar;  c.Label.String = 't_{ij}/t^0_{ij}';
hold on;
[X_ref, Y_ref] = meshgrid(phi_bpr, vc_bpr);
surf(X_ref, Y_ref, 1.15*ones(size(X_ref)),'FaceAlpha',0.12,'FaceColor',[0 0.7 0],'EdgeColor','none');
surf(X_ref, Y_ref, 2.00*ones(size(X_ref)),'FaceAlpha',0.08,'FaceColor',[0.8 0 0],'EdgeColor','none');
xlabel('\phi_{ij}  (Link Reliability)');
ylabel('V/C^0  (Volume/Capacity)');
zlabel('t_{ij}/t^0_{ij}  (Multiplier)');
title('M4 — BPR Congestion Surface: \phi_{ij} \times Volume/Capacity','FontWeight','bold');
view(25,-60);  grid on;
savefig(fig, fullfile(OUT_D,'M4_BPR_Surface.fig'));
fprintf('   Saved M4_BPR_Surface.fig\n');

% =========================================================================
%  M5  SQDR Analysis (3-panel)
% =========================================================================
fprintf('M5  SQDR analysis...\n');
T4 = readtable(fullfile(TABLE_D,'exp4.csv'));
phi_s  = sort(unique(T4.phi_min));
SR_s   = arrayfun(@(p) mean(T4.SR(T4.phi_min==p)),   phi_s);
OTSR_s = arrayfun(@(p) mean(T4.OTSR(T4.phi_min==p)), phi_s);
sqdr   = -gradient(SR_s, phi_s);
sqdr2  = -gradient(sqdr, phi_s);
[~,ki] = max(sqdr);

fig = figure('Position',[100 100 700 900]);

subplot(3,1,1);
plot(phi_s, SR_s, 'o-','Color',[0.08 0.40 0.75],'DisplayName','SR');
hold on;
plot(phi_s, OTSR_s,'s--','Color',[0.89 0.22 0.21],'DisplayName','OTSR');
xline(phi_s(ki),'--','Color',[1 0.6 0],'LineWidth',1.5,'Label','\phi^*');
xlabel('\phi_{min}'); ylabel('Rate (%)'); ylim([0 105]);
title('SR and OTSR vs \phi_{min}');  legend; grid on; set(gca,'XDir','reverse');

subplot(3,1,2);
plot(phi_s, sqdr, 'o-','Color',[0.42 0.00 0.62]);
hold on;
scatter(phi_s(ki), sqdr(ki), 120, [1 0.5 0], 'filled');
xline(phi_s(ki),'--','Color',[1 0.6 0],'LineWidth',1.5);
xlabel('\phi_{min}'); ylabel('SQDR = -\partial SR/\partial \phi_{min}');
title('Service Quality Degradation Rate');  grid on; set(gca,'XDir','reverse');

subplot(3,1,3);
plot(phi_s, sqdr2, 'o-','Color',[0.75 0.22 0.14]);
yline(0,'--','Color',[0.5 0.5 0.5]);
xline(phi_s(ki),'--','Color',[1 0.6 0],'LineWidth',1.5);
xlabel('\phi_{min}'); ylabel('\partial^2 SR/\partial \phi_{min}^2');
title('Degradation Acceleration');  grid on; set(gca,'XDir','reverse');

sgtitle('M5 — SQDR Knee Detection Analysis','FontWeight','bold','FontSize',13);
savefig(fig, fullfile(OUT_D,'M5_SQDR_Knee.fig'));
fprintf('   Saved M5_SQDR_Knee.fig\n');

% =========================================================================
%  M6  Failure Pattern Comparison
% =========================================================================
fprintf('M6  Failure patterns...\n');
T5     = readtable(fullfile(TABLE_D,'exp5.csv'));
patt   = {'random','progressive','clustered','hub'};
f_col  = [0.13 0.59 0.95; 1.00 0.60 0.00; 0.96 0.26 0.21; 0.61 0.15 0.69];
SR_p   = zeros(1,4); OTSR_p = zeros(1,4);
SR_sd  = zeros(1,4); OTSR_sd= zeros(1,4);
for pi=1:4
    mask = strcmp(T5.pattern, patt{pi});
    SR_p(pi)   = mean(T5.SR(mask));   SR_sd(pi)  = std(T5.SR(mask));
    OTSR_p(pi) = mean(T5.OTSR(mask)); OTSR_sd(pi)= std(T5.OTSR(mask));
end

fig = figure('Position',[100 100 900 450]);
subplot(1,2,1);
b = bar(SR_p,'FaceColor','flat');
for ci=1:4; b.CData(ci,:)=f_col(ci,:); end
hold on;
errorbar(1:4, SR_p, SR_sd, 'k.','LineWidth',1.5,'CapSize',6);
set(gca,'XTickLabel',{'Random','Progressive','Clustered','Hub'},'XTickLabelRotation',20);
ylabel('SR (%)');  title('Service Rate by Failure Pattern');
ylim([0 100]); grid on; box off;

subplot(1,2,2);
b2 = bar(OTSR_p,'FaceColor','flat');
for ci=1:4; b2.CData(ci,:)=f_col(ci,:); end
hold on;
errorbar(1:4, OTSR_p, OTSR_sd,'k.','LineWidth',1.5,'CapSize',6);
set(gca,'XTickLabel',{'Random','Progressive','Clustered','Hub'},'XTickLabelRotation',20);
ylabel('OTSR (%)'); title('On-Time Rate by Failure Pattern');
ylim([0 100]); grid on; box off;

sgtitle('M6 — Network Failure Pattern Impact (n=50, \phi_{min}=0.85)','FontWeight','bold');
savefig(fig, fullfile(OUT_D,'M6_Failure_Patterns.fig'));
fprintf('   Saved M6_Failure_Patterns.fig\n');

% =========================================================================
%  M7  Scalability (CT vs n, log-log)
% =========================================================================
fprintf('M7  Scalability...\n');
T6   = readtable(fullfile(TABLE_D,'exp6.csv'));
ns_s = sort(unique(T6.n));
fig  = figure('Position',[100 100 900 460]);

subplot(1,2,1);
algo_col = [0.13 0.59 0.95; 0.30 0.69 0.31;
            1.00 0.60 0.00; 0.96 0.26 0.21; 0.61 0.15 0.69];
lp = [];
for ai = 1:numel(ALGOS)
    ct_v = arrayfun(@(n) mean(T6.CT(T6.n==n & strcmp(T6.algo,ALGOS{ai}))), ns_s);
    h = loglog(ns_s, ct_v, 'o-','Color',algo_col(ai,:),'DisplayName',ALGOS{ai});
    lp(end+1) = h; hold on;
end
xlabel('n (log)'); ylabel('CT (s, log)'); title('Computation Time vs. n');
legend(lp,'Location','northwest'); grid on; box off;

subplot(1,2,2);
for ai = 1:numel(ALGOS)
    z_v = arrayfun(@(n) mean(T6.Z(T6.n==n & strcmp(T6.algo,ALGOS{ai}))), ns_s);
    plot(ns_s, z_v, 's--','Color',algo_col(ai,:),'DisplayName',ALGOS{ai});
    hold on;
end
xlabel('n'); ylabel('Z (mean, lower=better)'); title('Solution Quality vs. n');
legend('Location','northwest'); grid on; box off;

sgtitle('M7 — Scalability Analysis (\phi_{min}=0.85, Exp 6)','FontWeight','bold');
savefig(fig, fullfile(OUT_D,'M7_Scalability.fig'));
fprintf('   Saved M7_Scalability.fig\n');

% =========================================================================
%  M8  Network Topology Resilience  (Exp 8)
% =========================================================================
fprintf('M8  Topology resilience...\n');
T8    = readtable(fullfile(TABLE_D,'exp8.csv'));
topos = {'urban','suburban','rural','grid'};
t_col = [0.08 0.40 0.75; 0.18 0.55 0.18; 0.75 0.22 0.04; 0.42 0.00 0.62];
phi_t = sort(unique(T8.phi_min),'descend');

fig = figure('Position',[100 100 700 480]);
hold on;
ls_map = {'-','--','-.', ':'};
for ti = 1:numel(topos)
    sr_v = arrayfun(@(p) mean(T8.SR(T8.phi_min==p & strcmp(T8.topology,topos{ti}))), phi_t);
    plot(phi_t, sr_v, ls_map{ti},'Color',t_col(ti,:),'Marker','o','DisplayName',...
         [upper(topos{ti}(1)) topos{ti}(2:end)]);
end
set(gca,'XDir','reverse'); xlabel('\phi_{min}'); ylabel('SR (%)');
title('M8 — Topology Resilience: SR vs. \phi_{min}','FontWeight','bold');
legend('Location','southwest'); ylim([0 105]); grid on; box off;
savefig(fig, fullfile(OUT_D,'M8_Topology_Resilience.fig'));
fprintf('   Saved M8_Topology_Resilience.fig\n');

% =========================================================================
%  M9  3D Pareto Front  (synthetic — replace with real MOO output)
% =========================================================================
fprintf('M9  3D Pareto front...\n');
rng(42);
phi_sel  = [1.00 0.90 0.85 0.80 0.70];
p_colors = [0.08 0.40 0.75; 0.16 0.56 0.88; 1.00 0.60 0.00; 0.89 0.22 0.21; 0.61 0.15 0.69];

fig = figure('Position',[100 100 900 700]);
hold on;
for pi = 1:numel(phi_sel)
    phi  = phi_sel(pi);
    n    = 60;
    f1   = phi*0.55 + rand(n,1)*phi*0.45;
    f2   = 100/phi + rand(n,1)*80/phi;
    f3   = phi*0.85 + rand(n,1)*phi*0.15;
    scatter3(f3, f1, -f2, 30, 'filled',...
             'MarkerFaceColor', p_colors(pi,:),...
             'MarkerFaceAlpha', 0.70,...
             'DisplayName', sprintf('\\phi_{min}=%.2f',phi));
end
scatter3(1.0, 1.0, -100, 150, 'p','MarkerFaceColor','gold','MarkerEdgeColor','k',...
         'DisplayName','Utopia ★');
xlabel('f_3: Route Reliability'); ylabel('f_1: Satisfaction'); zlabel('-f_2: Efficiency');
title('M9 — 3D Pareto Front: f_1 \times f_2 \times f_3 (Exp 7)','FontWeight','bold');
legend('Location','northwest','NumColumns',2); grid on;
view(22, -55);
savefig(fig, fullfile(OUT_D,'M9_3D_Pareto_Front.fig'));
fprintf('   Saved M9_3D_Pareto_Front.fig\n');

% =========================================================================
%  DONE
% =========================================================================
fprintf('\nAll MATLAB .fig files saved to:\n  %s\n', OUT_D);
fprintf('Open any .fig file in MATLAB with: openfig(fullfile(OUT_D, ''M1_SR_vs_phi.fig''))\n');
